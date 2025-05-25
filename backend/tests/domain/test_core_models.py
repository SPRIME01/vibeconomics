import pytest
from uuid import UUID, uuid4
from typing import List
from pydantic import BaseModel

from app.core.base_aggregate import AggregateRoot, DomainEvent


class TestDomainEvent(DomainEvent):
    """Test domain event for testing purposes."""
    event_type: str
    data: str


class TestAggregate(AggregateRoot):
    """Test aggregate for testing purposes."""
    name: str

    def do_something(self, data: str) -> None:
        """Test method that generates a domain event."""
        event = TestDomainEvent(event_type="something_done", data=data)
        self.add_event(event)


class TestAggregateRoot:
    """Test cases for the AggregateRoot base class."""

    def test_aggregate_root_initializes_with_id(self) -> None:
        """Test that AggregateRoot can be initialized with a UUID id."""
        aggregate_id = uuid4()
        aggregate = TestAggregate(id=aggregate_id, name="test")

        assert aggregate.id == aggregate_id
        assert isinstance(aggregate.id, UUID)

    def test_aggregate_root_auto_generates_id_if_not_provided(self) -> None:
        """Test that AggregateRoot generates an id if none is provided."""
        aggregate = TestAggregate(name="test")

        assert aggregate.id is not None
        assert isinstance(aggregate.id, UUID)

    def test_add_event_stores_event_in_private_list(self) -> None:
        """Test that add_event stores events in a private list."""
        aggregate = TestAggregate(name="test")
        event = TestDomainEvent(event_type="test_event", data="test_data")

        aggregate.add_event(event)

        # Events should be stored but not directly accessible
        # We'll verify through pull_events
        events = aggregate.pull_events()
        assert len(events) == 1
        assert events[0] == event

    def test_add_multiple_events(self) -> None:
        """Test that multiple events can be added and stored."""
        aggregate = TestAggregate(name="test")
        event1 = TestDomainEvent(event_type="event_1", data="data_1")
        event2 = TestDomainEvent(event_type="event_2", data="data_2")

        aggregate.add_event(event1)
        aggregate.add_event(event2)

        events = aggregate.pull_events()
        assert len(events) == 2
        assert events[0] == event1
        assert events[1] == event2

    def test_pull_events_returns_all_stored_events(self) -> None:
        """Test that pull_events returns all stored events."""
        aggregate = TestAggregate(name="test")
        event1 = TestDomainEvent(event_type="event_1", data="data_1")
        event2 = TestDomainEvent(event_type="event_2", data="data_2")

        aggregate.add_event(event1)
        aggregate.add_event(event2)

        events = aggregate.pull_events()

        assert isinstance(events, list)
        assert len(events) == 2
        assert event1 in events
        assert event2 in events

    def test_pull_events_clears_internal_list(self) -> None:
        """Test that pull_events clears the internal events list."""
        aggregate = TestAggregate(name="test")
        event = TestDomainEvent(event_type="test_event", data="test_data")

        aggregate.add_event(event)

        # First pull should return the event
        first_pull = aggregate.pull_events()
        assert len(first_pull) == 1

        # Second pull should return empty list
        second_pull = aggregate.pull_events()
        assert len(second_pull) == 0

    def test_pull_events_returns_empty_list_when_no_events(self) -> None:
        """Test that pull_events returns empty list when no events are stored."""
        aggregate = TestAggregate(name="test")

        events = aggregate.pull_events()

        assert isinstance(events, list)
        assert len(events) == 0

    def test_domain_event_is_base_model(self) -> None:
        """Test that DomainEvent is a Pydantic BaseModel."""
        event = TestDomainEvent(event_type="test", data="test_data")

        assert isinstance(event, BaseModel)
        assert event.event_type == "test"
        assert event.data == "test_data"

    def test_aggregate_business_logic_can_generate_events(self) -> None:
        """Test that aggregate business methods can generate events through add_event."""
        aggregate = TestAggregate(name="test")

        aggregate.do_something("business_operation")

        events = aggregate.pull_events()
        assert len(events) == 1
        assert events[0].event_type == "something_done"
        assert events[0].data == "business_operation"

    def test_multiple_aggregates_have_separate_event_lists(self) -> None:
        """Test that different aggregate instances maintain separate event lists."""
        aggregate1 = TestAggregate(name="test1")
        aggregate2 = TestAggregate(name="test2")

        event1 = TestDomainEvent(event_type="event_1", data="data_1")
        event2 = TestDomainEvent(event_type="event_2", data="data_2")

        aggregate1.add_event(event1)
        aggregate2.add_event(event2)

        events1 = aggregate1.pull_events()
        events2 = aggregate2.pull_events()

        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0] == event1
        assert events2[0] == event2
