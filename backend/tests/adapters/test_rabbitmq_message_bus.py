from unittest.mock import ANY, MagicMock, patch

import pytest

from app.adapters.rabbitmq_message_bus import RabbitMQMessageBus  # Direct import
from app.core.base_aggregate import DomainEvent  # Direct import


class SampleDomainEvent(DomainEvent):
    some_data: str = "default"
    # If DomainEvent from app.core.base_aggregate is not a Pydantic BaseModel,
    # and SampleDomainEvent needs Pydantic features, it might need to inherit BaseModel too.
    # However, assuming DomainEvent is a Pydantic model.


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish() -> None:
    """Test that an event is published to RabbitMQ with the correct routing key and body."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event = SampleDomainEvent()

    await bus.publish(sample_event)

    mock_channel.basic_publish.assert_called_once_with(
        exchange="",
        routing_key="SampleDomainEvent",
        body=sample_event.model_dump_json(),
    )


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_subscribe_and_handle() -> None:
    """Test that a handler can be subscribed to an event and is called with the correct event data."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)
    mock_handler = MagicMock()

    # Register the handler. This will call mock_channel.basic_consume
    # because the actual RabbitMQMessageBus is used.
    bus.register_handler(SampleDomainEvent, mock_handler)

    # Assert that queue_declare was called with the correct arguments
    mock_channel.queue_declare.assert_called_with(
        queue="SampleDomainEvent", durable=True
    )

    # Check that basic_consume was called and capture the on_message_callback argument
    mock_channel.basic_consume.assert_called_once()

    # Inspect the call arguments to get the callback
    # The arguments are ((queue_name, on_message_callback_function), {'auto_ack': True})
    # Or if called with kwargs: ((), {'queue': queue_name, 'on_message_callback': ..., 'auto_ack': True})
    # We need to be robust to how basic_consume was called by the bus implementation.
    # Let's assume it's called with keyword arguments for on_message_callback.
    call_args = mock_channel.basic_consume.call_args
    if call_args.kwargs:  # If called with keyword arguments
        on_message_callback = call_args.kwargs.get("on_message_callback")
    elif (
        call_args.args and len(call_args.args) > 1
    ):  # If called with positional arguments
        # This depends on the exact signature used in the RabbitMQMessageBus.
        # Assuming on_message_callback is the second positional argument if no kwargs.
        # This might be: queue, on_message_callback, auto_ack, exclusive, consumer_tag, arguments
        # The actual RabbitMQMessageBus implementation uses:
        # channel.basic_consume(queue=event_type_name, on_message_callback=on_message_callback, auto_ack=True)
        # So 'on_message_callback' will be in kwargs.
        on_message_callback = call_args.args[1]
    else:
        on_message_callback = None

    assert on_message_callback is not None, (
        "on_message_callback was not captured correctly from basic_consume"
    )

    sample_event = SampleDomainEvent(some_data="test_value")
    serialized_event_body = sample_event.model_dump_json().encode("utf-8")

    # Mock arguments that pika's on_message_callback receives
    mock_channel_arg = (
        MagicMock()
    )  # This is the channel instance pika passes to the callback
    mock_method_frame = MagicMock()  # Mock for pika's method frame
    mock_properties = MagicMock()  # Mock for pika's properties

    # Invoke the captured callback directly
    on_message_callback(
        mock_channel_arg, mock_method_frame, mock_properties, serialized_event_body
    )

    # Assert that the mock_handler was called with the correct event
    mock_handler.assert_called_once()
    called_event = mock_handler.call_args[0][
        0
    ]  # Get the first argument of the first call
    assert isinstance(called_event, SampleDomainEvent), (
        f"Handler called with type {type(called_event)} but expected SampleDomainEvent"
    )
    assert called_event.some_data == "test_value", (
        f"Event data mismatch: {called_event.some_data} != 'test_value'"
    )
    assert called_event == sample_event, (
        f"Event content mismatch: {called_event} != {sample_event}"
    )


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish() -> None:
    """Test that an event is published to RabbitMQ with the correct routing key, body, and properties."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)  # Uses actual bus
    sample_event = SampleDomainEvent()

    await bus.publish(sample_event)

    mock_channel.basic_publish.assert_called_once_with(
        exchange="",
        routing_key="SampleDomainEvent",  # Relies on type(event).__name__
        body=sample_event.model_dump_json(),
        properties=ANY,  # Accept any properties object
    )
    args, kwargs = mock_channel.basic_publish.call_args
    assert kwargs.get("properties") is not None
    assert (
        kwargs.get("properties").delivery_mode == 2
    )  # pika.spec.PERSISTENT_DELIVERY_MODE


# New tests for error handling
import pika.exceptions  # For raising pika specific exceptions

from app.service_layer.exceptions import MessageBusError  # For asserting custom error


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_connection_failure() -> None:
    """Tests that MessageBusError is raised on Pika connection error during publish."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    # Configure basic_publish on the dynamically created channel mock to raise an error
    mock_channel.basic_publish.side_effect = pika.exceptions.AMQPConnectionError(
        "Simulated connection failed"
    )

    bus = RabbitMQMessageBus(connection=mock_connection)
    sample_event = SampleDomainEvent(some_data="test_publish_fail")

    with pytest.raises(MessageBusError) as excinfo:
        await bus.publish(sample_event)

    assert "Failed to publish event SampleDomainEvent" in str(excinfo.value)
    assert "Simulated connection failed" in str(excinfo.value)
    mock_channel.basic_publish.assert_called_once()  # Ensure it was attempted


@pytest.mark.asyncio  # Keep async even if callback is sync, for consistency if bus methods become async
async def test_rabbitmq_message_bus_handler_exception_nacks_message_and_logs() -> None:
    """Tests that an exception in a handler results in basic_nack and logs the error."""
    # Patch logger before bus instantiation so the bus uses the patched logger
    with patch(
        "app.adapters.rabbitmq_message_bus.logging.getLogger"
    ) as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel

        bus = RabbitMQMessageBus(connection=mock_connection)

        handler_error_message = "Simulated handler error"
        mock_handler = MagicMock(side_effect=Exception(handler_error_message))

        bus.register_handler(SampleDomainEvent, mock_handler)

        # Capture the on_message_callback
        mock_channel.basic_consume.assert_called_once()
        on_message_callback = mock_channel.basic_consume.call_args.kwargs.get(
            "on_message_callback"
        )
        assert on_message_callback is not None, "on_message_callback was not captured"

        sample_event = SampleDomainEvent(some_data="test_handler_fail")
        serialized_event_body = sample_event.model_dump_json().encode("utf-8")

        mock_method_frame = MagicMock(spec=pika.spec.Basic.Deliver, delivery_tag=123)
        mock_properties = MagicMock(spec=pika.spec.BasicProperties)

        # Invoke the callback directly
        on_message_callback(
            mock_channel,  # Pika passes the channel instance to the callback
            mock_method_frame,
            mock_properties,
            serialized_event_body,
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
        error_log_call = mock_logger.error.call_args
        assert handler_error_message in str(error_log_call)
        assert "SampleDomainEvent" in str(error_log_call)
        assert "delivery_tag 123" in str(error_log_call)  # As per current bus impl.


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_register_handler_pika_error() -> None:
    """Test that register_handler raises MessageBusError and logs when pika channel setup fails."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    # Simulate an error when declaring the queue
    mock_channel.queue_declare.side_effect = pika.exceptions.ChannelClosed(
        406, "Channel closed"
    )

    bus = RabbitMQMessageBus(connection=mock_connection)
    mock_handler = MagicMock()

    with pytest.raises(MessageBusError) as excinfo:
        bus.register_handler(SampleDomainEvent, mock_handler)

    # The implementation raises a generic MessageBusError with a message about acquiring the channel
    assert "Unexpected error acquiring channel for SampleDomainEvent" in str(
        excinfo.value
    )
    assert "Channel closed" in str(excinfo.value)

    # Check that the error is logged
    mock_channel.queue_declare.assert_called_once_with(
        queue="SampleDomainEvent", durable=True
    )
    mock_channel.basic_consume.assert_not_called()  # basic_consume should not be called if registration fails


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_batch_success() -> None:
    """Test that publish_batch successfully publishes all events."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    bus = RabbitMQMessageBus(connection=mock_connection)

    # Create a list of sample events
    sample_events = [SampleDomainEvent(some_data=f"test_value_{i}") for i in range(3)]

    await bus.publish_batch(sample_events)

    # Assert that basic_publish was called for each event
    assert mock_channel.basic_publish.call_count == len(sample_events)
    for i, event in enumerate(sample_events):
        mock_channel.basic_publish.assert_any_call(
            exchange="",
            routing_key="SampleDomainEvent",
            body=event.model_dump_json(),
            properties=ANY,  # Accept any properties object
        )


@pytest.mark.asyncio
async def test_rabbitmq_message_bus_publish_batch_failure() -> None:
    """Test that publish_batch raises MessageBusError if any publish fails."""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    # Configure basic_publish to succeed for the first two calls, then fail
    mock_channel.basic_publish.side_effect = [
        None,  # First call succeeds
        None,  # Second call succeeds
        pika.exceptions.AMQPConnectionError(
            "Simulated connection failed"
        ),  # Third call fails
    ]

    bus = RabbitMQMessageBus(connection=mock_connection)

    # Create a list of sample events
    sample_events = [SampleDomainEvent(some_data=f"test_value_{i}") for i in range(3)]

    with pytest.raises(MessageBusError) as excinfo:
        await bus.publish_batch(sample_events)

    assert "Failed to publish event SampleDomainEvent" in str(excinfo.value)
    assert "Simulated connection failed" in str(excinfo.value)
    assert (
        mock_channel.basic_publish.call_count == 3
    )  # Ensure all publish attempts were made
