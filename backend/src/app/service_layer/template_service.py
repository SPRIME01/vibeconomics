import re
from typing import Any

from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.template_extensions import (
    TemplateExtensionRegistry,
    create_memory_extensions,
)


class MissingVariableError(ValueError):
    """Raised when a required template variable is missing."""

    pass


class TemplateService:
    """Service for processing templates with variable substitution and extensions."""

    def __init__(self, memory_service: AbstractMemoryService | None = None):
        self.memory_service = memory_service
        self.extension_registry = TemplateExtensionRegistry()

        # Register memory extensions if memory service is available
        if self.memory_service:
            memory_extensions = create_memory_extensions(self.memory_service)
            for name, func in memory_extensions.items():
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

        # Process template extensions first
        processed_template = await self.extension_registry.process_template_extensions(
            template, variables
        )

        # Then process regular variable substitution
        return await self._render_variables(processed_template, variables)

    def process_template(self, template: str) -> str:
        """
        Synchronous method to process template with extensions only.
        This is for backward compatibility and testing.
        """
        import asyncio

        return asyncio.run(
            self.extension_registry.process_template_extensions(template, {})
        )

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
