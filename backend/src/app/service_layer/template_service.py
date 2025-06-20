import re
from typing import Any

from app.adapters.activepieces_adapter import AbstractActivePiecesAdapter
from app.adapters.a2a_client_adapter import A2AClientAdapter # Import A2AClientAdapter
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.template_extensions import (
    TemplateExtensionRegistry,
    create_activepieces_extensions,
    create_memory_extensions,
    create_a2a_extensions, # Import create_a2a_extensions
)


class MissingVariableError(ValueError):
    """Raised when a required template variable is missing."""

    pass


class TemplateService:
    """Service for processing templates with extensions."""

    def __init__(
        self,
        memory_service: AbstractMemoryService | None = None,
        activepieces_adapter: AbstractActivePiecesAdapter | None = None,
        a2a_client_adapter: A2AClientAdapter | None = None, # Add a2a_client_adapter
    ) -> None:
        """
        Initializes the TemplateService with optional adapters for memory, activepieces, and A2A client services.
        
        Registers available template extensions based on the provided adapters.
        """
        self.memory_service = memory_service
        self.activepieces_adapter = activepieces_adapter
        self.a2a_client_adapter = a2a_client_adapter # Store it
        self.extension_registry = TemplateExtensionRegistry()

        # Register extensions
        self._register_extensions()

    def _register_extensions(self) -> None:
        """
        Registers template extension functions from available adapters into the extension registry.
        
        This method adds extension functions provided by the memory service, activepieces adapter,
        and A2A client adapter (if present) to the template extension registry, making them
        available for use in template processing.
        """
        if self.memory_service:
            memory_extensions = create_memory_extensions(self.memory_service)
            for name, func in memory_extensions.items():
                self.extension_registry.register(name, func)

        if self.activepieces_adapter:
            activepieces_extensions = create_activepieces_extensions(
                self.activepieces_adapter
            )
            for name, func in activepieces_extensions.items():
                self.extension_registry.register(name, func)
        
        if self.a2a_client_adapter:
            # from app.service_layer.template_extensions import create_a2a_extensions # No longer needed here due to top import
            a2a_extensions = create_a2a_extensions(self.a2a_client_adapter)
            for name, func in a2a_extensions.items():
                self.extension_registry.register(name, func)

    async def render(
        self,
        template: str,
        variables: dict[str, Any],
        context_data: dict[str, Any] | None = None, # Renamed from context to context_data for clarity
    ) -> str:
        """
        Renders a template string by substituting variables and processing registered extensions.
        
        Args:
            template: The template string containing variable placeholders and extension calls.
            variables: Dictionary of values to substitute for variable placeholders.
            context_data: Optional dictionary with additional context; currently not used for dynamic extension registration.
        
        Returns:
            The fully rendered template string with variables and extensions processed.
        """
        # Note: The logic for dynamically registering extensions based on context_data
        # for memory_service was present. If a2a_client_adapter can also be passed this way,
        # similar dynamic registration could be added. For now, sticking to __init__ based registration.
        # If context_data contains 'a2a_client_adapter' and self.a2a_client_adapter was None,
        # one could initialize and register a2a_extensions here.

        # First, process template extensions. Extensions can modify the `variables` dict.
        template_after_extensions = await self.extension_registry.process_template_extensions(
            template,
            variables,
        )

        # Then, substitute simple {{variable}} placeholders on the result
        final_template = await self._render_variables(
            template_after_extensions, variables
        )
        return final_template

    # The synchronous process_template method seems to be an alternative rendering path
    # or an older version. It duplicates some logic from process_template_extensions
    # and doesn't seem to align with the async nature of render and A2A extensions.
    # For the purpose of this task, we are focusing on the async `render` method.
    # This synchronous method might need review or removal if it's redundant or conflicts.
    def process_template(
        self, template_content: str, variables: dict[str, Any] | None = None
    ) -> str:
        """
        Process a template with extensions and variables.

        Args:
            template_content: Template content with extension calls
            variables: Optional variables for template substitution

        Returns:
            Processed template content
        """
        if variables is None:
            variables = {}

        # Process extensions
        processed_template = template_content

        # Get all extension boundaries
        boundaries = self.extension_registry._find_extension_boundaries(
            template_content
        )

        # Debug: Print what we found
        print(f"Template: {template_content}")
        print(f"Found boundaries: {boundaries}")
        print(
            f"Available extensions: {list(self.extension_registry._extensions.keys())}"
        )

        # Process extensions from right to left to maintain positions
        for start_pos, end_pos, namespace, operation, args_str in reversed(boundaries):
            extension_name = f"{namespace}_{operation}"
            full_match_str = template_content[start_pos:end_pos]
            replacement_text = full_match_str

            print(f"Processing: {extension_name}, args: {args_str}")

            if extension_name in self.extension_registry._extensions:
                try:
                    extension_function = self.extension_registry._extensions[
                        extension_name
                    ]

                    # Parse arguments based on extension type
                    if extension_name == "activepieces_run_workflow":
                        if ":" in args_str:
                            workflow_id, input_data_str = args_str.split(":", 1)
                            args = [workflow_id.strip(), input_data_str.strip()]
                        else:
                            args = [args_str.strip(), "{}"]
                    elif extension_name == "memory_search":
                        if ":" in args_str:
                            user_id, query = args_str.split(":", 1)
                            args = [user_id.strip(), query.strip()]
                        else:
                            args = [args_str.strip()]
                    else:
                        args = [args_str.strip()] if args_str else []

                    print(f"Calling extension with args: {args}")
                    replacement_text = extension_function(*args)
                    print(f"Extension result: {replacement_text}")
                except Exception as e:
                    replacement_text = (
                        f"[ERROR IN EXTENSION: {extension_name} - {str(e)}]"
                    )
                    print(f"Extension error: {e}")
            else:
                print(f"Extension {extension_name} not found in registry")

            # Replace this specific occurrence
            processed_template = (
                processed_template[:start_pos]
                + replacement_text
                + processed_template[end_pos:]
            )

        return processed_template

    async def _render_variables(self, template: str, variables: dict[str, Any]) -> str:
        """Handle basic {{variable}} substitution."""

        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name not in variables:
                # It's crucial that extensions run first and populate variables.
                # If a variable is still not found here, it's genuinely missing.
                raise MissingVariableError(f"Missing variable: {var_name}")
            value = variables[var_name]
            
            # If the value is a dict or list (e.g. from an output_variable),
            # and it's being rendered directly into the template,
            # it should be JSON dumped to be valid.
            if isinstance(value, (dict, list)):
                import json # Ensure json is imported
                return json.dumps(value)
            return str(value) if value is not None else ""

        # Replace {{variable}} patterns that are not extensions (no colons and not extension tags)
        # This regex is simplified; it assumes that any {{...}} without colons is a variable.
        # More complex logic might be needed if {{...}} can appear in other contexts that aren't variables or extensions.
        result = re.sub(r"\{\{\s*([^}:}\s]+)\s*\}\}", replace_var, template) # Adjusted regex to be more specific for simple vars
        return result
