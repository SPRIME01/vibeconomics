from typing import Any
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService
from app.service_layer.commands.chat_commands import ProcessUserChatMessageCommand
# from app.service_layer.unit_of_work import AbstractUnitOfWork # Not needed per plan
# from app.domain.chat.repositories import ConversationRepository # Not needed per plan

class ProcessUserChatMessageCommandHandler:
    def __init__(
        self,
        ai_pattern_execution_service: AIPatternExecutionService,
    ):
        self.ai_pattern_execution_service = ai_pattern_execution_service

    async def handle(self, command: ProcessUserChatMessageCommand) -> Any:
        '''
        Handles the ProcessUserChatMessageCommand by executing a conversational pattern.

        Args:
            command: The command containing the user's message, session ID, and model choice.

        Returns:
            The response from the AIPatternExecutionService.
        '''
        
CONVERSATIONAL_CHAT_PATTERN = "conversational_chat"

        response = await self.ai_pattern_execution_service.execute_pattern(
            pattern_name=CONVERSATIONAL_CHAT_PATTERN, # Or "conversational_chat.md"
            input_variables={"input": command.user_message},
            session_id=command.session_id,
            model_name=command.model_choice,
        )
        
        return response
