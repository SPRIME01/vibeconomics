from typing import Any

from app.service_layer.unit_of_work import AbstractUnitOfWork


class FakeConversationRepository:
    """Fake repository for conversations used in testing."""

    def __init__(self):
        """Initialize the fake repository."""
        self._conversations: dict[str, Any] = {}

    async def get_by_id(self, conversation_id: str) -> Any | None:
        """Get a conversation by ID."""
        return self._conversations.get(str(conversation_id))

    async def create(self, conversation: Any) -> None:
        """Create a new conversation."""
        self._conversations[str(conversation.id)] = conversation

    async def save(self, conversation: Any) -> None:
        """Save an existing conversation."""
        self._conversations[str(conversation.id)] = conversation


class FakeUnitOfWork(AbstractUnitOfWork):
    """Fake unit of work implementation for testing."""

    def __init__(self):
        """Initialize the fake unit of work."""
        self.conversations = FakeConversationRepository()
        self.committed = False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        pass

    def __enter__(self):
        """Sync context manager entry."""
        return self

    def __exit__(self, *args):
        """Sync context manager exit."""
        pass

    async def commit(self):
        """Commit the transaction."""
        self.committed = True

    async def rollback(self):
        """Roll back the transaction."""
        pass
