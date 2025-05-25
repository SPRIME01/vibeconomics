import uuid

from app.adapters.mem0_adapter import AbstractMemoryRepository
from app.core.base_aggregate import (  # Added DomainEvent for AbstractMessageBus type hint
    AggregateId,
    DomainEvent,
)
from app.domain.memory.events import MemoryStoredEvent
from app.domain.memory.models import (  # Added MemoryWriteRequest
    MemoryId,
    MemoryWriteRequest,
)
from app.service_layer.commands.memory import StoreMemoryCommand  # Uncommented
from app.service_layer.message_bus import AbstractMessageBus
from app.service_layer.unit_of_work import AbstractUnitOfWork


class StoreMemoryCommandHandler:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        message_bus: AbstractMessageBus[DomainEvent],  # Specified generic type
        memory_repo: AbstractMemoryRepository,
    ):
        self.uow = uow
        self.message_bus = message_bus
        self.memory_repo = memory_repo

    async def handle(
        self, command: StoreMemoryCommand
    ) -> MemoryId | None:  # Restored type hint
        external_memory_id: str | None = None
        internal_memory_id: MemoryId | None = None

        with self.uow:  # Assuming self.uow handles commit/rollback
            write_request = MemoryWriteRequest(
                user_id=command.user_id,
                text_content=command.text_content,
                metadata=command.metadata,
            )
            external_memory_id = self.memory_repo.add(write_request)

            if not external_memory_id:
                # self.uow.rollback() # Or handle error appropriately
                return None

            # Ensure AggregateId is treated as uuid.UUID for MemoryId
            memory_item_aggregate_id = MemoryId(
                AggregateId(uuid.uuid4())
            )  # Create a new UUID for internal tracking
            internal_memory_id = memory_item_aggregate_id

            preview_length = 50
            text_preview = (
                (command.text_content[:preview_length] + "...")
                if len(command.text_content) > preview_length
                else command.text_content
            )

            event = MemoryStoredEvent(
                memory_id=internal_memory_id,
                user_id=command.user_id,
                text_content_preview=text_preview,
                external_id=external_memory_id,  # Store the ID from the external mem0 service
            )
            self.message_bus.publish(
                event
            )  # Assuming publish handles events within the UoW
            # self.uow.commit() # Or handled by the context manager
        return internal_memory_id
