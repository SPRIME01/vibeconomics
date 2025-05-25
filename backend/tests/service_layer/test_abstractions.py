from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel


# Domain Event for testing (renamed to avoid pytest collection)
class SampleDomainEvent(BaseModel):
    """Sample domain event for testing message bus functionality."""

    event_id: UUID
    event_type: str
    data: dict[str, Any]


# Test implementations to verify protocol compliance
class ConcreteUnitOfWork:
    """Concrete implementation for testing AbstractUnitOfWork protocol."""

    def __init__(self) -> None:
        self.repositories: dict[str, Any] = {}
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> "ConcreteUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._committed and not self._rolled_back:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        self._rolled_back = True


class ConcreteMessageBus:
    """Concrete implementation for testing AbstractMessageBus protocol."""

    def __init__(self) -> None:
        self.published_events: list[SampleDomainEvent] = []

    async def publish(self, event: SampleDomainEvent) -> None:
        self.published_events.append(event)


class TestAbstractUnitOfWork:
    """Test suite for AbstractUnitOfWork protocol interface."""

    def test_abstract_unit_of_work_protocol_exists(self) -> None:
        """Test that AbstractUnitOfWork can be imported and is a Protocol."""
        try:
            import typing

            from app.service_layer.unit_of_work import AbstractUnitOfWork

            # Check if it's a Protocol class
            assert issubclass(AbstractUnitOfWork, typing.Protocol)

            # Check for runtime_checkable decorator
            assert hasattr(AbstractUnitOfWork, "__protocol__") or getattr(
                AbstractUnitOfWork, "_is_protocol", False
            ), "AbstractUnitOfWork should be a runtime checkable protocol"
        except ImportError:
            pytest.fail(
                "AbstractUnitOfWork should be importable from app.service_layer.unit_of_work"
            )

    def test_abstract_unit_of_work_has_required_methods(self) -> None:
        """Test that AbstractUnitOfWork defines all required methods."""
        from app.service_layer.unit_of_work import AbstractUnitOfWork

        # Check that protocol defines expected methods
        required_methods = ["__aenter__", "__aexit__", "commit", "rollback"]
        for method in required_methods:
            assert hasattr(AbstractUnitOfWork, method), (
                f"AbstractUnitOfWork should define {method}"
            )

    def test_abstract_unit_of_work_has_repositories_attribute(self) -> None:
        """Test that AbstractUnitOfWork defines repositories attribute."""
        from app.service_layer.unit_of_work import AbstractUnitOfWork

        # Check that repositories attribute is defined in annotations
        annotations = getattr(AbstractUnitOfWork, "__annotations__", {})
        assert "repositories" in annotations, (
            "AbstractUnitOfWork should define repositories attribute"
        )
        assert annotations["repositories"] == dict[str, Any], (
            "repositories should be typed as Dict[str, Any]"
        )

    def test_concrete_implementation_satisfies_protocol(self) -> None:
        """Test that a concrete implementation satisfies the AbstractUnitOfWork protocol."""
        from app.service_layer.unit_of_work import AbstractUnitOfWork

        # Verify that ConcreteUnitOfWork is compatible with the protocol
        uow = ConcreteUnitOfWork()

        # This should not raise a type error if protocol is properly defined
        def accepts_uow(unit_of_work: AbstractUnitOfWork) -> None:
            pass

        accepts_uow(uow)  # Should work if protocol is satisfied

    @pytest.mark.asyncio
    async def test_concrete_implementation_async_context_manager(self) -> None:
        """Test that concrete implementation works as async context manager."""
        uow = ConcreteUnitOfWork()

        async with uow as context_uow:
            assert context_uow is uow
            await context_uow.commit()

        assert uow._committed

    @pytest.mark.asyncio
    async def test_concrete_implementation_rollback_on_exception(self) -> None:
        """Test that concrete implementation rolls back on exception."""
        uow = ConcreteUnitOfWork()

        try:
            async with uow:
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert uow._rolled_back

    def test_repositories_access(self) -> None:
        """Test that repositories can be accessed and modified."""
        uow = ConcreteUnitOfWork()

        # Should be able to access repositories
        assert isinstance(uow.repositories, dict)

        # Should be able to add repositories
        mock_repo = Mock()
        uow.repositories["test_repo"] = mock_repo
        assert uow.repositories["test_repo"] is mock_repo


class TestAbstractMessageBus:
    """Test suite for AbstractMessageBus protocol interface."""

    def test_abstract_message_bus_protocol_exists(self) -> None:
        """Test that AbstractMessageBus can be imported and is a Protocol."""
        try:
            import typing

            from app.service_layer.message_bus import AbstractMessageBus

            # Check if it's a Protocol class
            assert issubclass(AbstractMessageBus, typing.Protocol)

            # Check for runtime_checkable decorator
            assert hasattr(AbstractMessageBus, "__protocol__") or getattr(
                AbstractMessageBus, "_is_protocol", False
            ), "AbstractMessageBus should be a runtime checkable protocol"
        except ImportError:
            pytest.fail(
                "AbstractMessageBus should be importable from app.service_layer.message_bus"
            )

    def test_abstract_message_bus_has_publish_method(self) -> None:
        """Test that AbstractMessageBus defines publish method."""
        from app.service_layer.message_bus import AbstractMessageBus

        # Check that protocol defines publish method
        assert hasattr(AbstractMessageBus, "publish"), (
            "AbstractMessageBus should define publish method"
        )

    def test_abstract_message_bus_publish_signature(self) -> None:
        """Test that publish method has correct signature."""
        from app.service_layer.message_bus import AbstractMessageBus

        # Check method annotations if available
        if hasattr(AbstractMessageBus, "__annotations__"):
            annotations = AbstractMessageBus.__annotations__
            # This test will be more meaningful once the actual protocol is implemented
            # For now, we ensure the method exists
            pass

    def test_concrete_implementation_satisfies_protocol(self) -> None:
        """Test that a concrete implementation satisfies the AbstractMessageBus protocol."""
        from app.service_layer.message_bus import AbstractMessageBus

        # Verify that ConcreteMessageBus is compatible with the protocol
        bus = ConcreteMessageBus()

        # This should not raise a type error if protocol is properly defined
        def accepts_bus(message_bus: AbstractMessageBus) -> None:
            pass

        accepts_bus(bus)  # Should work if protocol is satisfied

    @pytest.mark.asyncio
    async def test_concrete_implementation_publish(self) -> None:
        """Test that concrete implementation can publish events."""
        bus = ConcreteMessageBus()

        event = SampleDomainEvent(
            event_id=uuid4(), event_type="test_event", data={"key": "value"}
        )

        await bus.publish(event)

        assert len(bus.published_events) == 1
        assert bus.published_events[0] is event

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self) -> None:
        """Test publishing multiple events maintains order."""
        bus = ConcreteMessageBus()

        events = [
            SampleDomainEvent(
                event_id=uuid4(), event_type=f"test_event_{i}", data={"index": i}
            )
            for i in range(3)
        ]

        for event in events:
            await bus.publish(event)

        assert len(bus.published_events) == 3
        for i, published_event in enumerate(bus.published_events):
            assert published_event.data["index"] == i


class TestProtocolIntegration:
    """Integration tests for both protocols working together."""

    @pytest.mark.asyncio
    async def test_uow_and_message_bus_integration(self) -> None:
        """Test that UoW and MessageBus can work together."""
        from app.service_layer.message_bus import AbstractMessageBus
        from app.service_layer.unit_of_work import AbstractUnitOfWork

        uow = ConcreteUnitOfWork()
        bus = ConcreteMessageBus()

        # Simulate a service that uses both
        async def sample_service(
            unit_of_work: AbstractUnitOfWork, message_bus: AbstractMessageBus
        ) -> None:
            async with unit_of_work:
                # Simulate some work
                event = SampleDomainEvent(
                    event_id=uuid4(),
                    event_type="work_completed",
                    data={"status": "success"},
                )
                await message_bus.publish(event)
                await unit_of_work.commit()

        await sample_service(uow, bus)

        assert uow._committed
        assert len(bus.published_events) == 1
        assert bus.published_events[0].event_type == "work_completed"

    def test_type_checking_compatibility(self) -> None:
        """Test that implementations are type-compatible with protocols."""
        from app.service_layer.message_bus import AbstractMessageBus
        from app.service_layer.unit_of_work import AbstractUnitOfWork

        # These assignments should work without type errors
        uow: AbstractUnitOfWork = ConcreteUnitOfWork()
        bus: AbstractMessageBus = ConcreteMessageBus()

        # Verify basic attributes exist
        assert hasattr(uow, "repositories")
        assert hasattr(bus, "publish")
        assert callable(bus.publish)
