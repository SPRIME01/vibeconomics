import pytest
from uuid import UUID, uuid4

from app.domain.agent.models import Conversation, ChatMessage
from app.adapters.conversation_repository_inmemory import (
    InMemoryConversationRepository,
    ConversationAlreadyExistsError,
)


@pytest.fixture
def repo() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()


@pytest.fixture
def sample_conversation_data() -> dict:
    # This fixture might not be directly used if Conversation objects are created in tests,
    # but it's good practice to have it if complex setup is needed.
    return {
        "id": uuid4(),
        "messages": [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!"),
        ],
    }


async def test_create_new_conversation(repo: InMemoryConversationRepository) -> None:
    conv_id = uuid4()
    conversation = Conversation(id=conv_id, messages=[ChatMessage(role="user", content="Hello")])
    await repo.create(conversation)
    retrieved = await repo.get_by_id(conv_id)
    assert retrieved is not None
    assert retrieved.id == conv_id
    assert len(retrieved.messages) == 1
    assert retrieved.messages[0].content == "Hello"
    # Ensure it's a copy and not the same object in memory
    assert retrieved is not conversation
    original_message_content = conversation.messages[0].content
    conversation.messages[0].content = "Modified internally" 
    assert retrieved.messages[0].content == original_message_content


async def test_create_existing_conversation_raises_error(repo: InMemoryConversationRepository) -> None:
    conv_id = uuid4()
    conversation = Conversation(id=conv_id)
    await repo.create(conversation)
    with pytest.raises(ConversationAlreadyExistsError):
        await repo.create(conversation) # Same instance
    
    conversation_same_id = Conversation(id=conv_id, messages=[ChatMessage(role="user", content="Different instance")])
    with pytest.raises(ConversationAlreadyExistsError):
        await repo.create(conversation_same_id) # Different instance, same ID


async def test_get_by_id_existing(repo: InMemoryConversationRepository) -> None:
    conv_id = uuid4()
    conversation = Conversation(id=conv_id, messages=[ChatMessage(role="user", content="Test message")])
    await repo.create(conversation)
    retrieved = await repo.get_by_id(conv_id)
    assert retrieved is not None
    assert retrieved.id == conv_id
    assert len(retrieved.messages) == 1
    assert retrieved.messages[0].content == "Test message"
    assert retrieved is not conversation # Ensure it's a copy


async def test_get_by_id_non_existent(repo: InMemoryConversationRepository) -> None:
    retrieved = await repo.get_by_id(uuid4())
    assert retrieved is None


async def test_save_new_conversation(repo: InMemoryConversationRepository) -> None:
    conv_id = uuid4()
    conversation = Conversation(id=conv_id, messages=[ChatMessage(role="user", content="New save")])
    await repo.save(conversation)
    retrieved = await repo.get_by_id(conv_id)
    assert retrieved is not None
    assert retrieved.id == conv_id
    assert retrieved.messages[0].content == "New save"
    assert retrieved is not conversation # Ensure copy


async def test_save_updates_existing_conversation(repo: InMemoryConversationRepository) -> None:
    conv_id = uuid4()
    conversation = Conversation(id=conv_id, messages=[ChatMessage(role="user", content="Initial content")])
    await repo.create(conversation) # First create it

    # Modify the original instance (though repo should have a copy)
    conversation.add_message(role="assistant", content="Updated content")
    
    # Create a new instance for saving, or use a copy of the modified one
    # This ensures we are testing the save functionality correctly.
    # If we saved 'conversation' directly after modifying it, and if 'create' didn't make a copy,
    # this test might pass for the wrong reasons.
    modified_conversation_to_save = Conversation(id=conv_id, messages=conversation.messages[:]) # Create a new instance with modified messages

    await repo.save(modified_conversation_to_save)
    
    retrieved = await repo.get_by_id(conv_id)
    assert retrieved is not None
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].content == "Initial content"
    assert retrieved.messages[1].content == "Updated content"
    assert retrieved is not modified_conversation_to_save # Ensure copy


async def test_save_and_get_multiple_conversations(repo: InMemoryConversationRepository) -> None:
    conv1_id = uuid4()
    conv1 = Conversation(id=conv1_id, messages=[ChatMessage(role="user", content="Conv 1 User")])
    await repo.save(conv1)

    conv2_id = uuid4()
    conv2 = Conversation(id=conv2_id, messages=[ChatMessage(role="user", content="Conv 2 User")])
    await repo.save(conv2)
    
    conv1_retrieved = await repo.get_by_id(conv1_id)
    assert conv1_retrieved is not None
    assert conv1_retrieved.id == conv1_id
    assert conv1_retrieved.messages[0].content == "Conv 1 User"
    assert conv1_retrieved is not conv1

    conv2_retrieved = await repo.get_by_id(conv2_id)
    assert conv2_retrieved is not None
    assert conv2_retrieved.id == conv2_id
    assert conv2_retrieved.messages[0].content == "Conv 2 User"
    assert conv2_retrieved is not conv2

    # Quick check to ensure they are distinct after retrieval
    assert conv1_retrieved.messages[0].content != conv2_retrieved.messages[0].content

    # Modify conv1, save it, and ensure conv2 is not affected
    conv1_retrieved.add_message(role="assistant", content="Conv 1 Assistant")
    await repo.save(conv1_retrieved)

    conv1_re_retrieved = await repo.get_by_id(conv1_id)
    assert conv1_re_retrieved is not None
    assert len(conv1_re_retrieved.messages) == 2
    assert conv1_re_retrieved.messages[1].content == "Conv 1 Assistant"

    conv2_re_retrieved = await repo.get_by_id(conv2_id) # Re-retrieve conv2
    assert conv2_re_retrieved is not None
    assert len(conv2_re_retrieved.messages) == 1 # Should still have only 1 message
    assert conv2_re_retrieved.messages[0].content == "Conv 2 User"
