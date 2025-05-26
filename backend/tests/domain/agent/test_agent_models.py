from datetime import datetime, timezone, timedelta
import time
from uuid import UUID

from app.core.base_aggregate import AggregateRoot
from app.domain.agent.events import ConversationMessageAddedEvent
from app.domain.agent.models import ChatMessage, Conversation


def test_chat_message_creation() -> None:
    message = ChatMessage(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_conversation_is_aggregate_root() -> None:
    conversation = Conversation()
    assert isinstance(conversation, AggregateRoot)
    assert hasattr(conversation, "id")
    assert isinstance(conversation.id, UUID)


def test_conversation_initialization() -> None:
    conversation = Conversation()
    assert conversation.messages == []
    # Test timestamps on creation
    now = datetime.now(timezone.utc)
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.last_updated_at, datetime)
    assert conversation.created_at.tzinfo == timezone.utc
    assert now - conversation.created_at < timedelta(seconds=1)
    assert conversation.last_updated_at == conversation.created_at


def test_add_message_to_conversation() -> None:
    conversation = Conversation()
    initial_created_at = conversation.created_at
    initial_last_updated_at = conversation.last_updated_at

    # Ensure a discernible time difference for last_updated_at
    time.sleep(0.01) 

    conversation.add_message(role="user", content="Hello")
    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"
    assert conversation.messages[0].content == "Hello"
    
    # Test timestamp updates
    assert conversation.created_at == initial_created_at
    assert conversation.last_updated_at > initial_last_updated_at
    assert conversation.last_updated_at.tzinfo == timezone.utc
    assert datetime.now(timezone.utc) - conversation.last_updated_at < timedelta(seconds=1)

    # Add another message to ensure last_updated_at is updated again
    initial_last_updated_at_after_first_message = conversation.last_updated_at
    time.sleep(0.01)

    conversation.add_message(role="assistant", content="Hi there")
    assert len(conversation.messages) == 2
    assert conversation.created_at == initial_created_at
    assert conversation.last_updated_at > initial_last_updated_at_after_first_message


def test_get_messages_from_conversation() -> None:
    conversation = Conversation()
    conversation.add_message(role="user", content="First message")
    conversation.add_message(role="assistant", content="Second message")

    retrieved_messages = conversation.get_messages()

    assert retrieved_messages is conversation.messages
    assert len(retrieved_messages) == 2
    assert retrieved_messages[0].content == "First message"
    assert retrieved_messages[1].content == "Second message"


def test_add_message_raises_event() -> None:
    conversation = Conversation()
    assert not conversation.domain_events

    test_content1 = "This is a test message for event."
    conversation.add_message(role="user", content=test_content1)
    assert len(conversation.domain_events) == 1
    event1 = conversation.domain_events[0]
    assert isinstance(event1, ConversationMessageAddedEvent)
    assert event1.conversation_id == conversation.id
    assert event1.role == "user"
    assert event1.content_preview == test_content1[:50]

    test_content2 = "Another message to trigger a second event."
    conversation.add_message(role="assistant", content=test_content2)
    assert len(conversation.domain_events) == 2
    event2 = conversation.domain_events[1]
    assert isinstance(event2, ConversationMessageAddedEvent)
    assert event2.conversation_id == conversation.id
    assert event2.role == "assistant"
    assert event2.content_preview == test_content2[:50]
