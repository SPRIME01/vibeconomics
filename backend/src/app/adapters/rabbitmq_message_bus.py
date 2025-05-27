import json
import logging # Added
from typing import Callable, Type, Dict, List

import pika
import pika.spec
import pika.exceptions # Already imported but good to confirm
from pydantic import ValidationError

from app.core.base_aggregate import DomainEvent
from app.service_layer.message_bus import AbstractMessageBus
from app.service_layer.exceptions import MessageBusError # Added


class RabbitMQMessageBus(AbstractMessageBus):
    def __init__(self, connection: pika.BlockingConnection) -> None:
        self._connection: pika.BlockingConnection = connection
        self._handlers: Dict[str, Callable[[DomainEvent], None]] = {}
        self._event_types: Dict[str, Type[DomainEvent]] = {} # To store event class for deserialization
        # It's good practice to get a logger instance per module
        self._logger = logging.getLogger(__name__)

    def _perform_publish(self, channel: pika.channel.Channel, routing_key: str, body: str) -> None:
        """Helper method to perform the actual basic_publish call."""
        channel.basic_publish(
            exchange='',
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

    async def publish(self, event: DomainEvent) -> None:
        channel = None
        routing_key = type(event).__name__ # Used in logging and MessageBusError
        try:
            channel = self._connection.channel()
            # Ensure queue exists for routing, durable to survive broker restart
            channel.queue_declare(queue=routing_key, durable=True)

            body = event.model_dump_json()
            
            self._perform_publish(channel, routing_key, body)
            self._logger.info(f"Successfully published event {routing_key}")
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.ChannelClosedByBroker,
            pika.exceptions.StreamLostError,
            pika.exceptions.ChannelWrongStateError
        ) as e:
            self._logger.error(f"Failed to publish event {routing_key}: {e}", exc_info=True)
            raise MessageBusError(f"Failed to publish event {routing_key}: {e}") from e
            if channel and channel.is_open:
                try:
                    channel.close()
                    self._logger.debug(f"Closed channel for publishing event {routing_key}")
                except Exception as e:
                    # Log an error if closing the channel fails, but don't let it overshadow the original exception
                    self._logger.warning(f"Error closing channel after publishing event {routing_key}: {e}", exc_info=True)


    async def publish_batch(self, events: List[DomainEvent]) -> None:
        # This will propagate MessageBusError from the first failed publish
        for event in events:
            await self.publish(event)

    def _setup_channel_for_event_handler(
        self, 
        channel: pika.channel.Channel, 
        event_type_name: str, 
        on_message_callback_func: Callable[
            [pika.channel.Channel, pika.spec.Basic.Deliver, pika.spec.BasicProperties, bytes], 
            None
        ]
    ) -> None:
        """Helper method to declare queue and set up consumer for an event type."""
        try:
            channel.queue_declare(queue=event_type_name, durable=True)
            channel.basic_consume(
                queue=event_type_name,
                on_message_callback=on_message_callback_func,
                auto_ack=False # Manual acknowledgment
            )
            self._logger.info(f"Declared queue and started consuming for {event_type_name} with manual ACK.")
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.ChannelClosedByBroker,
            pika.exceptions.StreamLostError,
            pika.exceptions.ChannelWrongStateError
        ) as e:
            # Log the error and raise a MessageBusError to indicate failure in setup
            self._logger.error(f"Failed to set up channel for event handler {event_type_name}: {e}", exc_info=True)
            raise MessageBusError(f"Failed to set up channel for event handler {event_type_name}: {e}") from e


    def register_handler(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        event_type_name = event_type.__name__
        self._handlers[event_type_name] = handler
        self._event_types[event_type_name] = event_type # Store event class for deserialization

        # The on_message_callback needs access to self, event_type_name, etc.
        # Defining it as a nested function captures these from the surrounding scope.
        def on_message_callback_internal(
            ch: pika.channel.Channel, # Renamed to avoid conflict with outer scope 'channel' if any
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes
        ) -> None:
            # The routing_key or queue name should tell us the event type name
            # Assuming queue name is the event_type_name as per current setup
            # If method.routing_key is more reliable, use that.
            # For basic_consume on a specific queue, that queue's name is the key.
            
            # This callback is registered per queue, and we named the queue after event_type_name.
            # The 'event_type_name' string is captured from the outer scope of register_handler.
            
            # Retrieve the actual DomainEvent subclass for deserialization
            specific_event_type_class = self._event_types.get(event_type_name)

            if not specific_event_type_class:
                self._logger.error(f"No event type class found for event_type_name '{event_type_name}'. Message body: {body[:200]}. NACKing.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            try:
                self._logger.debug(f"Received message for event '{event_type_name}', delivery_tag {method.delivery_tag}")
                event_obj = specific_event_type_class.model_validate_json(body.decode('utf-8'))
                
                # Retrieve the actual handler function
                actual_handler = self._handlers[event_type_name]
                actual_handler(event_obj) # Execute the domain handler
                
                self._logger.info(f"Successfully processed event '{event_type_name}', delivery_tag {method.delivery_tag}. ACK.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except (json.JSONDecodeError, ValidationError) as e:
                decoded_body = body.decode('utf-8', errors='replace')
                max_log_length = 200
                sanitized_body = (decoded_body[:max_log_length] + '... [truncated]') if len(decoded_body) > max_log_length else decoded_body
                self._logger.error(
                    f"Failed to decode or validate message for event '{event_type_name}': {sanitized_body}, error: {e}. NACKing.",
                    exc_info=True
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                self._logger.error(f"Error processing message for event '{event_type_name}', delivery_tag {method.delivery_tag}: {e}. Body: {body[:200]}. NACKing.", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        # Obtain a channel for this registration
        # The lifecycle of this channel needs consideration. If it's one channel per registration,
        # it should be managed (e.g., stored if it needs to be accessed later for cancellation).
        # For BlockingConnection, channel operations are synchronous.
        try:
            channel = self._connection.channel()
            self._setup_channel_for_event_handler(channel, event_type_name, on_message_callback_internal)
        except MessageBusError: # Propagate error if setup fails
            # The _setup_channel_for_event_handler already logs the specific pika error
            self._logger.error(f"Failed to register handler for {event_type_name} due to channel setup issues.")
            raise # Re-raise the MessageBusError
        except Exception as e: # Catch any other unexpected errors during channel acquisition
            self._logger.error(f"An unexpected error occurred while acquiring channel for {event_type_name}: {e}", exc_info=True)
            raise MessageBusError(f"Unexpected error acquiring channel for {event_type_name}: {e}") from e

    def start_consuming(self) -> None:
        # This method might be needed if the connection is run in a separate thread
        # and start_consuming needs to be called on channels.
        # For BlockingConnection, often channel.start_consuming() is called,
        # which blocks. If handlers are on multiple queues/channels, this needs careful management.
        # For now, tests pass by directly invoking the callback, so a full consuming loop
        # isn't strictly necessary for this step.
        # If we have multiple consumers (channels consuming), each would need its start_consuming call,
        # typically each in its own thread.
        
        # A simple way if only one channel is used for all consumption, or if called per channel:
        # try:
        #     print("Starting to consume messages...")
        #     # Assuming a single channel for now, or that this is called on the relevant channel.
        #     # This is a blocking call.
        #     # self._connection.channel().start_consuming() # This would need channel to be stored if used like this.
        # except KeyboardInterrupt:
        #     print("Consumption stopped.")
        # finally:
        #     if self._connection.is_open:
        #         self._connection.close()
        pass # Placeholder, as tests trigger callbacks directly.
```
