import re
from typing import Any

from .memory_service import MemoryService
from .template_extensions import (
    TemplateExtensionRegistry,
    create_memory_extensions,
    process_template_extensions,
)


class MissingVariableError(Exception):
    """Raised when a required template variable is missing."""

    pass


class TemplateService:
    """Service for processing templates with variable substitution and extensions."""

    def __init__(self, memory_service: MemoryService | None = None) -> None:
        self._extension_registry = TemplateExtensionRegistry()

        # Register memory extensions if memory service is provided
        if memory_service:
            memory_extensions = create_memory_extensions(memory_service)
            for name, func in memory_extensions.items():
                self._extension_registry.register(name, func)

    def render(self, template_content: str, variables: dict[str, Any]) -> str:
        """
        Render template with variable substitution.

        Args:
            template_content: Template content with {{variable}} placeholders
            variables: Dictionary of variables to substitute

        Returns:
            Rendered template content

        Raises:
            MissingVariableError: If a required variable is missing
        """
        # Find all variable placeholders
        variable_pattern = r"\{\{([^}:]+)\}\}"

        def replace_variable(match: re.Match[str]) -> str:
            var_name = match.group(1).strip()
            if var_name not in variables:
                raise MissingVariableError(f"Missing variable: {var_name}")
            return str(variables[var_name])

        return re.sub(variable_pattern, replace_variable, template_content)

    def process_template(
        self, template_content: str, variables: dict[str, Any] | None = None
    ) -> str:
        """
        Process template with both extensions and variable substitution.

        Args:
            template_content: Template content with extensions and variables
            variables: Optional variables for substitution

        Returns:
            Fully processed template content
        """
        if variables is None:
            variables = {}

        # First process extensions
        processed_content = process_template_extensions(
            template_content, self._extension_registry
        )

        # Then process any remaining variables (extensions might not use variable syntax)
        try:
            return self.render(processed_content, variables)
        except MissingVariableError:
            # If there are no variables to substitute, just return the processed content
            return processed_content
