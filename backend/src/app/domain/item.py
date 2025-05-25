from uuid import UUID

from app.core.base_aggregate import AggregateRoot


class Item(AggregateRoot):
    name: str
    description: str | None = None
    owner_id: UUID


# Ensure there is a newline character at the end of this file.
