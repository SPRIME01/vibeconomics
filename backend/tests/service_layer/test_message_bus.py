import pytest
from unittest.mock import MagicMock
from typing import Type
import logging # Required for caplog to work with logger in message_bus

from app.core.base_aggregate import DomainEvent
from app.service_layer.message_bus import AbstractMessageBus, EventT # EventT might not be strictly needed for test
from app.adapters.message_bus_inmemory import InMemoryMessageBus # Test this concrete impl

# Import LogCaptureFixture for caplog type hint
from _pytest.logging import LogCaptureFixture


class EventA(DomainEvent):
    value: int

class EventB(DomainEvent):
    message: str

def test_inmemory_message_bus_subscribe_and_publish() -> None:
    """Test that handlers are called for subscribed events."""
    bus: AbstractMessageBus[DomainEvent] = InMemoryMessageBus()
    
    handler_a1_mock = MagicMock()
    handler_a2_mock = MagicMock()
    handler_b_mock = MagicMock()

    bus.subscribe(EventA, handler_a1_mock)
    bus.subscribe(EventA, handler_a2_mock)
    bus.subscribe(EventB, handler_b_mock)

    event_a_instance = EventA(value=123)
    event_b_instance = EventB(message="hello")

    bus.publish(event_a_instance)
    handler_a1_mock.assert_called_once_with(event_a_instance)
    handler_a2_mock.assert_called_once_with(event_a_instance)
    handler_b_mock.assert_not_called()

    handler_a1_mock.reset_mock()
    handler_a2_mock.reset_mock()

    bus.publish(event_b_instance)
    handler_a1_mock.assert_not_called()
    handler_a2_mock.assert_not_called()
    handler_b_mock.assert_called_once_with(event_b_instance)

def test_inmemory_message_bus_no_handler() -> None:
    """Test publishing an event with no subscribers does not error."""
    bus: AbstractMessageBus[DomainEvent] = InMemoryMessageBus()
    event_a_instance = EventA(value=456)
    try:
        bus.publish(event_a_instance)
    except Exception as e:
        pytest.fail(f"Publishing event with no handlers raised an exception: {e}")

def test_inmemory_message_bus_handler_exception_does_not_stop_others(caplog: LogCaptureFixture) -> None: # Added type hint
    """Test that an exception in one handler doesn't prevent others from running."""
    bus: AbstractMessageBus[DomainEvent] = InMemoryMessageBus()
    
    # Set the log level for the logger used in InMemoryMessageBus to ensure messages are captured
    # This is important if the default level for this logger is higher than DEBUG or INFO
    # logger = logging.getLogger("app.adapters.message_bus_inmemory") # Get the specific logger
    # original_level = logger.level
    # logger.setLevel(logging.DEBUG) # Set to DEBUG to capture debug logs

    # Using caplog.at_level to temporarily set log level for the context of this test
    with caplog.at_level(logging.DEBUG, logger="app.adapters.message_bus_inmemory"):

        def faulty_handler(event: EventA) -> None:
            raise ValueError("Handler Error")

        handler_ok_mock = MagicMock()

        bus.subscribe(EventA, faulty_handler)
        bus.subscribe(EventA, handler_ok_mock)

        event_a_instance = EventA(value=789)
        bus.publish(event_a_instance)

        handler_ok_mock.assert_called_once_with(event_a_instance)
        assert "Exception handling event" in caplog.text
        assert "ValueError: Handler Error" in caplog.text
    
    # # Restore original log level if changed
    # logger.setLevel(original_level)
