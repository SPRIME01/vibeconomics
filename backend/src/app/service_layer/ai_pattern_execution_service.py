import inspect
from typing import Any  # For type hinting module_class
from uuid import UUID, uuid4

# Imports for execute_dspy_module
import dspy

# Note: If more DSPy modules are added to fabric_patterns.py, update this import accordingly.
from pydantic import BaseModel, ValidationError

from app.adapters.a2a_client_adapter import A2AClientAdapter  # Import A2AClientAdapter
from app.domain.agent.models import Conversation
from app.service_layer.ai_provider_service import AIProviderService
from app.service_layer.context_service import ContextService
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.pattern_service import PatternService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.template_service import TemplateService
from app.service_layer.unit_of_work import AbstractUnitOfWork


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
        a2a_client_adapter: A2AClientAdapter | None = None,  # Add a2a_client_adapter
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
        self.a2a_client_adapter = a2a_client_adapter  # Store a2a_client_adapter

    async def execute_dspy_module(
        self,
        module_class: type[dspy.Module],
        module_input: Any,
        **kwargs: Any,  # These kwargs are intended for the module's constructor
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
            NotImplementedError: If module_input is a dictionary and cannot be safely mapped to forward's parameters.
        """
        constructor_args = kwargs.copy()
        module_signature_params = inspect.signature(module_class.__init__).parameters

        if "a2a_adapter" in module_signature_params:
            if self.a2a_client_adapter:
                constructor_args["a2a_adapter"] = self.a2a_client_adapter
            else:
                raise AttributeError(
                    f"{module_class.__name__} requires an 'a2a_adapter', but it's not available in AIPatternExecutionService."
                )

        # Note on LLM Configuration for DSPy:
        # DSPy modules require an LLM to be configured via dspy.settings.configure(lm=your_lm).
        # This service assumes that the LM is configured elsewhere globally (e.g., application startup, or test setup).
        # A check could be added here: if not dspy.settings.lm: logging.warning("DSPy LM not configured globally.")
        import logging

        if not getattr(dspy.settings, "lm", None):
            logging.warning(
                "DSPy LM is not configured globally. Please call dspy.settings.configure(lm=...) before using DSPy modules."
            )

        module_instance = module_class(**constructor_args)

        # Use the unbound forward method for signature inspection
        forward_sig = inspect.signature(module_class.forward)
        forward_params = list(forward_sig.parameters.values())[1:]  # skip 'self'

        if isinstance(module_input, dict):
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in forward_params):
                result = await module_instance.forward(**module_input)
            elif all(
                k in [p.name for p in forward_params] for k in module_input.keys()
            ):
                result = await module_instance.forward(**module_input)
            else:
                raise NotImplementedError(
                    "module_input is a dictionary, but cannot be safely mapped to the forward method's parameters. "
                    "Explicitly match module_input keys to the forward signature or refactor the module."
                )
        elif len(forward_params) == 1:
            # Single argument expected (besides self), pass module_input as is
            result = await module_instance.forward(module_input)
        else:
            raise NotImplementedError(
                "module_input is not a dictionary, but forward expects multiple arguments. "
                "Explicitly provide a dictionary matching the forward signature."
            )
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
                            prompt_parts.append(f"{msg.role.upper()}: {msg.content}")
                        prompt_parts.append("=== End History ===\n")
                else:
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
        pattern_content = self.pattern_service.get_pattern_content(pattern_name) # Removed await
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
        if self.a2a_client_adapter:  # Pass adapter to template context
            template_context_data["a2a_client_adapter"] = self.a2a_client_adapter

        # Render the final prompt with template extensions support
        rendered_prompt = await self.template_service.render(
            template=base_prompt,
            variables=enhanced_variables,
            context_data=template_context_data,  # Pass the dictionary here
        )

        if not rendered_prompt or rendered_prompt.strip() == "":
            raise EmptyRenderedPromptError(
                "The prompt rendered from the template is empty or whitespace."
            )

        ai_response_content = await self.ai_provider_service.get_completion(
            prompt=rendered_prompt, model_name=model_name
        )

        # Session Saving (within UoW)
        async with self.uow:
            # Use the first string value from input_variables if only one key, else str(input_variables)
            if len(input_variables) == 1:
                user_message = next(iter(input_variables.values()))
            else:
                user_message = str(input_variables)

            if conversation:
                conversation.add_message(role="user", content=user_message)
                conversation.add_message(role="assistant", content=ai_response_content)
                await self.uow.conversations.save(conversation)
            else:
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
                raise e

        return ai_response_content
