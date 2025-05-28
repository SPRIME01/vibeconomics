from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError

from app.domain.agent.models import Conversation
from app.service_layer.ai_provider_service import AIProviderService
from app.service_layer.context_service import ContextService
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.pattern_service import PatternService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.template_service import TemplateService
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.adapters.a2a_client_adapter import A2AClientAdapter # Import A2AClientAdapter

# Imports for execute_dspy_module
import dspy
import inspect
from typing import Type # For type hinting module_class
from app.service_layer.fabric_patterns import CollaborativeRAGModule # Example module


class EmptyRenderedPromptError(ValueError):
    pass


class AIPatternExecutionService:
    def __init__(
        self,
        pattern_service: PatternService,
        template_service: TemplateService,
        strategy_service: StrategyService,
        context_service: ContextService,
        ai_provider_service: AIProviderService,
        uow: AbstractUnitOfWork,
        memory_service: AbstractMemoryService | None = None,
        a2a_client_adapter: A2AClientAdapter | None = None, # Add a2a_client_adapter
    ):
        """
        Initializes the AI pattern execution service with required domain and provider services.
        
        This constructor sets up the service with dependencies for pattern management, template rendering, strategy and context retrieval, AI provider interaction, unit-of-work management, and optional memory and A2A client adapter services.
        """
        self.pattern_service = pattern_service
        self.template_service = template_service
        self.strategy_service = strategy_service
        self.context_service = context_service
        self.ai_provider_service = ai_provider_service
        self.uow = uow
        self.memory_service = memory_service
        self.a2a_client_adapter = a2a_client_adapter # Store a2a_client_adapter

    async def execute_dspy_module(
        self,
        module_class: Type[dspy.Module],
        module_input: Any,
        **kwargs: Any, # These kwargs are intended for the module's constructor
    ) -> Any:
        """
        Instantiates and executes a DSPy module.

        Args:
            module_class: The class of the DSPy module to instantiate (e.g., CollaborativeRAGModule).
            module_input: The primary input for the module's `forward` method.
                          If the forward method expects a single positional argument, this is it.
                          If it expects keyword arguments, module_input should be a dictionary
                          that will be unpacked (e.g. `**module_input`).
                          For CollaborativeRAGModule, this is `input_question`.
            **kwargs: Additional keyword arguments for instantiating the module.

        Returns:
            The result from the module's `forward` method.
        
        Raises:
            AttributeError: If a2a_adapter is required by module but not available in service.
            NotImplementedError: If module_input is a dictionary for kwarg passing to forward,
                                 as this needs more robust signature inspection of forward.
        """
        constructor_args = kwargs.copy()
        module_signature_params = inspect.signature(module_class.__init__).parameters

        if "a2a_adapter" in module_signature_params:
            a2a_param = module_signature_params["a2a_adapter"]
            has_default = a2a_param.default is not inspect.Parameter.empty
            if self.a2a_client_adapter:
                constructor_args["a2a_adapter"] = self.a2a_client_adapter
            elif not has_default:
                # Module requires a2a_adapter (no default), but service doesn't have one.
                raise AttributeError(
                    f"{module_class.__name__} requires an 'a2a_adapter', but it's not available in AIPatternExecutionService."
                )
            # else: a2a_adapter is optional, so do nothing
        
        # Note on LLM Configuration for DSPy:
        # DSPy modules require an LLM to be configured via dspy.settings.configure(lm=your_lm).
        # This service assumes that the LM is configured elsewhere globally (e.g., application startup, or test setup).
        # A check could be added here: if not dspy.settings.lm: logging.warning("DSPy LM not configured globally.")
        
        module_instance = module_class(**constructor_args)

        # Executing the forward method.
        # The current CollaborativeRAGModule.forward takes `input_question: str`.
        # If module_input is a dict and forward expects kwargs, use **module_input.
        # For now, we assume module_input directly maps to the first arg of forward or is handled by the module.
        # A more robust solution would inspect `module_instance.forward` signature.
        if isinstance(module_input, dict) and not (len(inspect.signature(module_instance.forward).parameters) == 1 and next(iter(inspect.signature(module_instance.forward).parameters)) == 'self'):
             # Check if forward takes kwargs by inspecting its signature
            forward_params = inspect.signature(module_instance.forward).parameters
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in forward_params.values()): # **kwargs present
                result = await module_instance.forward(**module_input)
            elif all(k in forward_params for k in module_input.keys()): # all keys in module_input are named params
                 result = await module_instance.forward(**module_input)
            else:
                # This case is ambiguous: module_input is a dict, but forward doesn't clearly take **kwargs
                # or all keys as named parameters. We'll pass it as a single dict argument.
                # This might be an error for modules not expecting a dict as their first arg.
                # Example: CollaborativeRAGModule expects input_question (str), not a dict.
                # The user of execute_dspy_module must ensure module_input matches the forward method's expectation.
                # For CollaborativeRAGModule, module_input should be the string for input_question.
                # If module_input *is* the dict of kwargs for forward, then the signature above should be different.
                # The subtask mentioned "module_instance.forward(module_input)", implying direct pass.
                # Let's stick to direct pass for a single argument.
                # If module_input is a dict and intended for multiple args in forward, the caller needs to be specific.
                # For now, this path will assume module_input is the single expected argument.
                # This means if module_input is a dict, it's passed as that dict object.
                 result = await module_instance.forward(module_input)

        else: # module_input is not a dict, or forward is simple (e.g. only self)
            result = await module_instance.forward(module_input)
            
        return result

    async def execute_pattern(
        self,
        pattern_name: str,
        input_variables: dict[str, Any],
        session_id: UUID | None = None,
        strategy_name: str | None = None,
        context_name: str | None = None,
        model_name: str | None = None,
        output_model: type[BaseModel] | None = None,
    ) -> Any:
        """
        Executes an AI pattern by assembling prompt components, rendering the prompt, invoking AI completion, and managing conversation state.
        
        Args:
            pattern_name: The name of the AI pattern to execute.
            input_variables: Variables to be used for prompt rendering and AI completion.
            session_id: Optional conversation session identifier for maintaining context.
            strategy_name: Optional strategy to influence prompt construction.
            context_name: Optional context to include in the prompt.
            model_name: Optional AI model name for completion.
            output_model: Optional Pydantic model class for structured output parsing.
        
        Returns:
            The AI response as a string, or a parsed Pydantic model instance if `output_model` is provided.
        
        Raises:
            EmptyRenderedPromptError: If the rendered prompt is empty or contains only whitespace.
            ValidationError: If parsing the AI response into the specified output model fails.
        """
        conversation: Conversation | None = None
        prompt_parts: list[str] = []

        # Session Loading / Creation (within UoW)
        async with self.uow:
            if session_id:
                conversation = await self.uow.conversations.get_by_id(session_id)
                if conversation:
                    # Format conversation history properly for the prompt
                    history_messages = conversation.get_messages()
                    if history_messages:
                        prompt_parts.append("=== Conversation History ===")
                        for msg in history_messages:
                            # Format each message clearly for the AI
                            prompt_parts.append(f"{msg.role.upper()}: {msg.content}")
                        prompt_parts.append("=== End History ===\n")
                else:
                    # session_id provided but no conversation found, create a new one with this ID
                    conversation = Conversation(id=session_id)

        # Strategy Assembly
        if strategy_name:
            strategy = await self.strategy_service.get_strategy(strategy_name)
            if strategy and strategy.prompt:
                prompt_parts.append(f"=== Strategy ===\n{strategy.prompt}\n")

        # Context Assembly
        if context_name:
            context_content = await self.context_service.get_context_content(
                context_name
            )
            if context_content:
                prompt_parts.append(f"=== Context ===\n{context_content}\n")

        # Pattern Assembly
        pattern_content = await self.pattern_service.get_pattern_content(pattern_name)
        if pattern_content:
            prompt_parts.append(f"=== Current Task ===\n{pattern_content}")

        # Combine all parts into base prompt
        base_prompt = "\n".join(prompt_parts)

        # Enhanced input variables with memory service access
        enhanced_variables = input_variables.copy()

        # Make memory service available to template extensions if provided
        template_context_data = {}
        if self.memory_service:
            template_context_data["memory_service"] = self.memory_service
        if self.a2a_client_adapter: # Pass adapter to template context
            template_context_data["a2a_client_adapter"] = self.a2a_client_adapter

        # Render the final prompt with template extensions support
        rendered_prompt = await self.template_service.render(
            template=base_prompt,
            variables=enhanced_variables,
            context_data=template_context_data, # Pass the dictionary here
        )

        if not rendered_prompt or rendered_prompt.strip() == "":
            raise EmptyRenderedPromptError(
                "The prompt rendered from the template is empty or whitespace."
            )

        # Get AI Completion
        ai_response_content = await self.ai_provider_service.get_completion(
            prompt=rendered_prompt, model_name=model_name
        )

        # Session Saving (within UoW)
        async with self.uow:
            # Create user message from the current input (not the full rendered prompt)
            user_message = input_variables.get("input", str(input_variables))

            if conversation:
                conversation.add_message(role="user", content=user_message)
                conversation.add_message(role="assistant", content=ai_response_content)
                await self.uow.conversations.save(conversation)
            else:
                # Create new conversation
                new_conv_id = uuid4()
                conversation = Conversation(id=new_conv_id)
                conversation.add_message(role="user", content=user_message)
                conversation.add_message(role="assistant", content=ai_response_content)
                await self.uow.conversations.create(conversation)

            await self.uow.commit()

        # Handle structured output if requested
        if output_model:
            try:
                parsed_response = output_model.model_validate_json(ai_response_content)
                return parsed_response
            except ValidationError as e:
                # Log the error and re-raise for now
                raise e

        return ai_response_content
