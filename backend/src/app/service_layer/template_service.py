from typing import Any, Dict
import re

class MissingVariableError(Exception):
    """Custom exception for missing variables in a template."""
    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        super().__init__(f"Missing variable: {variable_name}")

class TemplateService:
    """Service for rendering templates."""

    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Renders a template string with the given variables.

        Args:
            template_content: The template string with {{variable}} placeholders.
            variables: A dictionary of variable names to their values.

        Returns:
            The rendered string.

        Raises:
            MissingVariableError: If a variable in the template is not found in the variables dict.
        """
        # Find all variable placeholders (e.g., {{name}})
        required_variables = re.findall(r"\{\{(.*?)\}\}", template_content)

        rendered_content = template_content
        for var_name in required_variables:
            # Strip whitespace from var_name as re.findall might include it
            clean_var_name = var_name.strip()
            if clean_var_name not in variables:
                raise MissingVariableError(clean_var_name)
            rendered_content = rendered_content.replace(f"{{{{{var_name}}}}}", str(variables[clean_var_name]))
        
        return rendered_content
