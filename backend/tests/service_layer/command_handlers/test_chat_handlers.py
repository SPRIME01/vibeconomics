import unittest
from unittest.mock import MagicMock, AsyncMock # AsyncMock for async methods

from app.service_layer.command_handlers.chat_handlers import ProcessUserChatMessageCommandHandler
from app.service_layer.commands.chat_commands import ProcessUserChatMessageCommand
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService
# AbstractUnitOfWork is not directly used by the handler, so no mock needed for it here.

class TestProcessUserChatMessageCommandHandler(unittest.IsolatedAsyncioTestCase): # Use IsolatedAsyncioTestCase for async tests

    async def test_handle_process_user_chat_message_command(self):
        mock_ai_pattern_service = MagicMock(spec=AIPatternExecutionService)
        # Configure the mock execute_pattern to be an AsyncMock if it's awaited
        mock_ai_pattern_service.execute_pattern = AsyncMock(return_value="Mocked AI Response")

        handler = ProcessUserChatMessageCommandHandler(
            ai_pattern_execution_service=mock_ai_pattern_service
        )

        command = ProcessUserChatMessageCommand(
            user_message="Hello AI!",
            session_id="test_session_123",
            model_choice="gpt-4",
            # user_id="test_user_abc", # Add if part of your command structure
            # persona_id="test_persona_xyz" # Add if part of your command structure
        )

        # Act
        result = await handler.handle(command)

        # Assert
        mock_ai_pattern_service.execute_pattern.assert_called_once_with(
            pattern_name="conversational_chat",
            input_variables={"input": "Hello AI!"},
            session_id="test_session_123",
            model_name="gpt-4",
            # persona_id="test_persona_xyz", # Add if expected
            # user_id="test_user_abc" # Add if expected
        )
        self.assertEqual(result, "Mocked AI Response")

    async def test_handle_returns_whatever_service_returns(self):
        mock_ai_pattern_service = MagicMock(spec=AIPatternExecutionService)
        expected_response_object = {"data": "some structured response", "status": "success"}
        mock_ai_pattern_service.execute_pattern = AsyncMock(return_value=expected_response_object)

        handler = ProcessUserChatMessageCommandHandler(
            ai_pattern_execution_service=mock_ai_pattern_service
        )

        command = ProcessUserChatMessageCommand(
            user_message="Another message",
            session_id="session_456",
            model_choice="claude-2"
        )
        
        result = await handler.handle(command)
        self.assertEqual(result, expected_response_object)

if __name__ == '__main__':
    unittest.main()
