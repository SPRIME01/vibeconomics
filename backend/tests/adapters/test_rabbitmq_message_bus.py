import asyncio
from unittest.mock import MagicMock, patch
from typing import Any

import pytest
from pydantic import BaseModel

from app.core.base_aggregate import DomainEvent
from app.adapters.rabbitmq_message_bus import RabbitMQMessageBus

class SampleDomainEvent(DomainEvent):
    some_data: str = "default"


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_subscribe_and_handle() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    mock_handler = MagicMock()

    bus.register_handler(SampleDomainEvent, mock_handler)

    mock_channel.queue_declare.assert_called_with(queue='SampleDomainEvent', durable=True)

    mock_channel.basic_consume.assert_called_once()

    call_args = mock_channel.basic_consume.call_args
    on_message_callback = call_args.kwargs.get('on_message_callback')

    assert on_message_callback is not None, "on_message_callback was not captured correctly from basic_consume"

    sample_event = SampleDomainEvent(some_data="test_value")
    serialized_event_body = sample_event.model_dump_json().encode('utf-8')

    mock_channel_arg = MagicMock()
    mock_method_frame = MagicMock()
    mock_properties = MagicMock()

    on_message_callback(
        mock_channel_arg, 
        mock_method_frame, 
        mock_properties, 
        serialized_event_body
    )

    mock_handler.assert_called_once()
    called_event = mock_handler.call_args[0][0]
    assert isinstance(called_event, SampleDomainEvent)
    assert called_event.some_data == "test_value"
    assert called_event == sample_event


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
        properties=MagicMock()
    )

    args, kwargs = mock_channel.basic_publish.call_args
    assert kwargs.get('properties') is not None
    assert kwargs.get('properties').delivery_mode == 2


import logging
import pika.exceptions
from app.service_layer.exceptions import MessageBusError

@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_connection_failure() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel
    
    mock_channel.basic_publish.side_effect = pika.exceptions.AMQPConnectionError("Simulated connection failed")

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event = SampleDomainEvent(some_data="test_publish_fail")

    with pytest.raises(MessageBusError) as excinfo:
        await bus.publish(sample_event)
    
    assert "Failed to publish event SampleDomainEvent" in str(excinfo.value)
    assert "Simulated connection failed" in str(excinfo.value)
    mock_channel.basic_publish.assert_called_once()


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_handler_exception_nacks_message_and_logs() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    
    handler_error_message = "Simulated handler error"
    mock_handler = MagicMock(side_effect=Exception(handler_error_message))
    
    bus.register_handler(SampleDomainEvent, mock_handler)

    mock_channel.basic_consume.assert_called_once()
    on_message_callback = mock_channel.basic_consume.call_args.kwargs.get('on_message_callback')
    assert on_message_callback is not None, "on_message_callback was not captured"

    sample_event = SampleDomainEvent(some_data="test_handler_fail")
    serialized_event_body = sample_event.model_dump_json().encode('utf-8')

    mock_method_frame = MagicMock(spec=pika.spec.Basic.Deliver, delivery_tag=123)
    mock_properties = MagicMock(spec=pika.spec.BasicProperties)

    mock_logger_on_bus = MagicMock()
    with patch.object(bus, '_logger', new=mock_logger_on_bus):
        on_message_callback(
            mock_channel,
            mock_method_frame, 
            mock_properties, 
            serialized_event_body
        )

    mock_handler.assert_called_once()
    called_event_arg = mock_handler.call_args[0][0]
    assert isinstance(called_event_arg, SampleDomainEvent)
    assert called_event_arg.some_data == sample_event.some_data

    mock_channel.basic_ack.assert_not_called()
    mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=False)
    
    mock_logger_on_bus.error.assert_called()
    error_log_call = mock_logger_on_bus.error.call_args
    assert handler_error_message in str(error_log_call)
    assert "SampleDomainEvent" in str(error_log_call)
    assert "delivery_tag 123" in str(error_log_call)


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_register_handler_pika_error() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    mock_handler = MagicMock()

    mock_channel.queue_declare.side_effect = pika.exceptions.AMQPConnectionError("Simulated queue declare error")

    with pytest.raises(MessageBusError) as excinfo:
        bus.register_handler(SampleDomainEvent, mock_handler)
    
    assert "Failed to set up channel for event handler SampleDomainEvent" in str(excinfo.value)
    assert "Simulated queue declare error" in str(excinfo.value)
    mock_channel.queue_declare.assert_called_once()


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_batch_success() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event1 = SampleDomainEvent(some_data="event1")
    sample_event2 = SampleDomainEvent(some_data="event2")

    await bus.publish_batch([sample_event1, sample_event2])

    assert mock_channel.basic_publish.call_count == 2


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_batch_failure() -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event1 = SampleDomainEvent(some_data="event1")
    sample_event2 = SampleDomainEvent(some_data="event2")

    mock_channel.basic_publish.side_effect = pika.exceptions.AMQPConnectionError("Simulated connection failed")

    with pytest.raises(MessageBusError) as excinfo:
        await bus.publish_batch([sample_event1, sample_event2])
    
    assert "Failed to publish event SampleDomainEvent" in str(excinfo.value)
    assert "Simulated connection failed" in str(excinfo.value)
    assert mock_channel.basic_publish.call_count == 1
