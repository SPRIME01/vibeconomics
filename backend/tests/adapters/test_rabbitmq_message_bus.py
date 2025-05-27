import asyncio
from unittest.mock import MagicMock, patch
from typing import Any # Removed Callable and Type as they are not directly used after placeholder removal

import pytest
from pydantic import BaseModel # Keep for SampleDomainEvent if it doesn't inherit from actual DomainEvent

from app.core.base_aggregate import DomainEvent # Direct import
from app.adapters.rabbitmq_message_bus import RabbitMQMessageBus # Direct import

class SampleDomainEvent(DomainEvent):
    some_data: str = "default"
    # If DomainEvent from app.core.base_aggregate is not a Pydantic BaseModel,
    # and SampleDomainEvent needs Pydantic features, it might need to inherit BaseModel too.
    # However, assuming DomainEvent is a Pydantic model.


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event = SampleDomainEvent()

    await bus.publish(sample_event)

    mock_channel.basic_publish.assert_called_once_with(
        exchange='',
        routing_key='SampleDomainEvent',
        body=sample_event.model_dump_json(),
    )


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_subscribe_and_handle() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    mock_handler = MagicMock()

    # Register the handler. This will call mock_channel.basic_consume
    # because the actual RabbitMQMessageBus is used.
    bus.register_handler(SampleDomainEvent, mock_handler)

    # Check that basic_consume was called and capture the on_message_callback argument
    mock_channel.basic_consume.assert_called_once()
    
    # Inspect the call arguments to get the callback
    # The arguments are ((queue_name, on_message_callback_function), {'auto_ack': True})
    # Or if called with kwargs: ((), {'queue': queue_name, 'on_message_callback': ..., 'auto_ack': True})
    # We need to be robust to how basic_consume was called by the bus implementation.
    # Let's assume it's called with keyword arguments for on_message_callback.
    call_args = mock_channel.basic_consume.call_args
    if call_args.kwargs: # If called with keyword arguments
        on_message_callback = call_args.kwargs.get('on_message_callback')
    elif call_args.args and len(call_args.args) > 1: # If called with positional arguments
        # This depends on the exact signature used in the RabbitMQMessageBus.
        # Assuming on_message_callback is the second positional argument if no kwargs.
        # This might be: queue, on_message_callback, auto_ack, exclusive, consumer_tag, arguments
        # The actual RabbitMQMessageBus implementation uses:
        # channel.basic_consume(queue=event_type_name, on_message_callback=on_message_callback, auto_ack=True)
        # So 'on_message_callback' will be in kwargs.
        on_message_callback = call_args.args[1] 
    else:
        on_message_callback = None

    assert on_message_callback is not None, "on_message_callback was not captured correctly from basic_consume"

    sample_event = SampleDomainEvent(some_data="test_value")
    serialized_event_body = sample_event.model_dump_json().encode('utf-8')

    # Mock arguments that pika's on_message_callback receives
    mock_channel_arg = MagicMock() # This is the channel instance pika passes to the callback
    mock_method_frame = MagicMock() # Mock for pika's method frame
    mock_properties = MagicMock()   # Mock for pika's properties

    # Invoke the captured callback directly
    on_message_callback(
        mock_channel_arg, 
        mock_method_frame, 
        mock_properties, 
        serialized_event_body
    )

    # Assert that the mock_handler was called with the correct event
    mock_handler.assert_called_once()
    called_event = mock_handler.call_args[0][0] # Get the first argument of the first call
    assert isinstance(called_event, SampleDomainEvent), \
        f"Handler called with type {type(called_event)} but expected SampleDomainEvent"
    assert called_event.some_data == "test_value", \
        f"Event data mismatch: {called_event.some_data} != 'test_value'"
    assert called_event == sample_event, \
        f"Event content mismatch: {called_event} != {sample_event}"

# The test_rabbitmq_message_bus_publish test seems to have been duplicated or truncated
# in the prompt. I will ensure it is correctly placed and complete.
# The following is the original test_rabbitmq_message_bus_publish method,
# which should remain as is.

@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection) # Uses actual bus
    sample_event = SampleDomainEvent()

    await bus.publish(sample_event)

    mock_channel.basic_publish.assert_called_once_with(
        exchange='',
        routing_key='SampleDomainEvent', # Relies on type(event).__name__
        body=sample_event.model_dump_json(),
        properties=MagicMock() # The actual implementation adds properties
    )
    # Refinement: Check properties more specifically if needed, e.g., delivery_mode
    # For now, MagicMock() checks that some properties object was passed.
    # To be more precise:
    # properties_arg = mock_channel.basic_publish.call_args.kwargs.get('properties')
    # assert properties_arg is not None
    # assert properties_arg.delivery_mode == pika.spec.PERSISTENT_DELIVERY_MODE
    # This would require importing pika into the test file.
    # For now, let's keep it simpler by asserting it was called with some properties.
    # The actual RabbitMQMessageBus passes: pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
    # So, we can make the assertion more specific if pika is imported.
    # Let's import pika.spec for this.

    # Adjusting the assertion for properties:
    args, kwargs = mock_channel.basic_publish.call_args
    assert kwargs.get('properties') is not None
    assert kwargs.get('properties').delivery_mode == 2 # pika.spec.PERSISTENT_DELIVERY_MODE


# New tests for error handling
import logging # For patching logger
import pika.exceptions # For raising pika specific exceptions
from app.service_layer.exceptions import MessageBusError # For asserting custom error

@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_connection_failure() -> None:
    """Tests that MessageBusError is raised on Pika connection error during publish."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel
    
    # Configure basic_publish on the dynamically created channel mock to raise an error
    mock_channel.basic_publish.side_effect = pika.exceptions.AMQPConnectionError("Simulated connection failed")

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event = SampleDomainEvent(some_data="test_publish_fail")

    with pytest.raises(MessageBusError) as excinfo:
        await bus.publish(sample_event)
    
    assert "Failed to publish event SampleDomainEvent" in str(excinfo.value)
    assert "Simulated connection failed" in str(excinfo.value)
    mock_channel.basic_publish.assert_called_once() # Ensure it was attempted


@pytest.mark.asyncio # Keep async even if callback is sync, for consistency if bus methods become async
async def test_rabbitmq_message_bus_handler_exception_nacks_message_and_logs() -> None:
    """Tests that an exception in a handler results in basic_nack and logs the error."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    
    handler_error_message = "Simulated handler error"
    mock_handler = MagicMock(side_effect=Exception(handler_error_message))
    
    bus.register_handler(SampleDomainEvent, mock_handler)

    # Capture the on_message_callback
    mock_channel.basic_consume.assert_called_once()
    on_message_callback = mock_channel.basic_consume.call_args.kwargs.get('on_message_callback')
    assert on_message_callback is not None, "on_message_callback was not captured"

    sample_event = SampleDomainEvent(some_data="test_handler_fail")
    serialized_event_body = sample_event.model_dump_json().encode('utf-8')

    mock_method_frame = MagicMock(spec=pika.spec.Basic.Deliver, delivery_tag=123)
    mock_properties = MagicMock(spec=pika.spec.BasicProperties)

    # Patch the logger used by RabbitMQMessageBus instance
    # Assuming logger is obtained via logging.getLogger('app.adapters.rabbitmq_message_bus')
    # or similar in RabbitMQMessageBus.__init__
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Invoke the callback directly
        on_message_callback(
            mock_channel, # Pika passes the channel instance to the callback
            mock_method_frame, 
            mock_properties, 
            serialized_event_body
        )

    # Assertions
    mock_handler.assert_called_once()
    called_event_arg = mock_handler.call_args[0][0]
    assert isinstance(called_event_arg, SampleDomainEvent)
    assert called_event_arg.some_data == sample_event.some_data

    mock_channel.basic_ack.assert_not_called()
    mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=False)
    
    # Check that logger.error was called and contains relevant info
    mock_logger.error.assert_called()
    # Example: Check if the error message or event type was logged.
    # This depends on the exact log message format in RabbitMQMessageBus.
    # For a robust check, you might need to inspect call_args more deeply.
    error_log_call = mock_logger.error.call_args
    assert handler_error_message in str(error_log_call)
    assert "SampleDomainEvent" in str(error_log_call)
    assert "delivery_tag 123" in str(error_log_call) # As per current bus impl.
