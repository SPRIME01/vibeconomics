import re
from typing import Any

from app.adapters.activepieces_adapter import AbstractActivePiecesAdapter
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.template_extensions import (
    TemplateExtensionRegistry,
    create_activepieces_extensions,
    create_memory_extensions,
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
    ) -> None:
        self.memory_service = memory_service
        self.activepieces_adapter = activepieces_adapter
        self.extension_registry = TemplateExtensionRegistry()

        # Register extensions
        self._register_extensions()

    def _register_extensions(self) -> None:
        """Register available template extensions."""
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

    async def render(
        self,
        template: str,
        variables: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render a template with variables and optional context.

        Args:
            template: Template string with {{variable}} and {{extension:operation:args}} syntax
            variables: Dictionary of variables to substitute
            context: Optional context containing services like memory_service

        Returns:
            Rendered template string
        """
        # Update memory service from context if provided
        if context and "memory_service" in context:
            memory_service = context["memory_service"]
            if memory_service and not self.memory_service:
                # Dynamically register memory extensions if not already done
                memory_extensions = create_memory_extensions(memory_service)
                for name, func in memory_extensions.items():
                    self.extension_registry.register(name, func)
                self.memory_service = memory_service

        # First, substitute simple variables
        variable_substituted_template = await self._render_variables(
            template, variables
        )

        # Then, process template extensions on the result
        final_template = await self.extension_registry.process_template_extensions(
            variable_substituted_template,
            variables,  # Pass variables, though not used by current ext processor
        )
        return final_template

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
                raise MissingVariableError(f"Missing variable: {var_name}")
            value = variables[var_name]
            return str(value) if value is not None else ""

        # Replace {{variable}} patterns that are not extensions (no colons)
        result = re.sub(r"\{\{([^}:]+)\}\}", replace_var, template)
        return result
