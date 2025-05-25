from typing import Optional
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.message_bus import AbstractMessageBus
from app.adapters.mem0_adapter import AbstractMemoryRepository
from app.domain.memory.models import MemoryItem, MemoryId, MemoryWriteRequest # Added MemoryWriteRequest
from app.domain.memory.events import MemoryStoredEvent
from app.service_layer.commands.memory import StoreMemoryCommand
from app.core.base_aggregate import AggregateId, DomainEvent # Added DomainEvent for AbstractMessageBus type hint

import uuid

class StoreMemoryCommandHandler:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        message_bus: AbstractMessageBus[DomainEvent], # Specified generic type
        memory_repo: AbstractMemoryRepository,
    ):
        self.uow = uow
        self.message_bus = message_bus
        self.memory_repo = memory_repo

    async def handle(self, command: StoreMemoryCommand) -> Optional[MemoryId]:
        external_memory_id: Optional[str] = None
        internal_memory_id: Optional[MemoryId] = None

        with self.uow:
            write_request = MemoryWriteRequest(
                user_id=command.user_id,
                text_content=command.text_content,
                metadata=command.metadata
            )
            external_memory_id = self.memory_repo.add(write_request)

            if not external_memory_id:
                return None

            # Ensure AggregateId is treated as uuid.UUID for MemoryId
            memory_item_aggregate_id = MemoryId(AggregateId(uuid.uuid4()))
            internal_memory_id = memory_item_aggregate_id

            preview_length = 50
            text_preview = (command.text_content[:preview_length] + '...') \
                if len(command.text_content) > preview_length else command.text_content
            
            event = MemoryStoredEvent(
                memory_id=internal_memory_id,
                user_id=command.user_id,
                text_content_preview=text_preview,
                external_id=external_memory_id
            )
            self.message_bus.publish(event)
        return internal_memory_id
