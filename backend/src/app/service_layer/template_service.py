from typing import Any, Dict, Callable
import re

class MissingVariableError(Exception):
    """Custom exception for missing variables in a template."""
    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        super().__init__(f"Missing variable: {variable_name}")

class UnknownExtensionError(Exception):
    """Custom exception for unknown extensions."""
    def __init__(self, namespace: str, operation: str):
        self.namespace = namespace
        self.operation = operation
        super().__init__(f"Unknown extension: {namespace}:{operation}")

class TemplateService:
    """Service for rendering templates."""

    def __init__(self, dependencies: Dict[str, Any] = None):
        self.extension_functions: Dict[str, Callable] = {}
        self.dependencies = dependencies if dependencies is not None else {}

    def register_extension(self, namespace: str, operation: str, func: Callable) -> None:
        """Registers an extension function."""
        self.extension_functions[f"{namespace}:{operation}"] = func

    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Renders a template string with the given variables and extensions.

        Args:
            template_content: The template string with {{variable}} or {{namespace:operation:key=val}} placeholders.
            variables: A dictionary of variable names to their values.

        Returns:
            The rendered string.

        Raises:
            MissingVariableError: If a variable in the template is not found in the variables dict.
            UnknownExtensionError: If an extension in the template is not registered.
        """
        rendered_content = template_content

        # Process extensions first
        # Regex to find extensions: {{namespace:operation:args}} or {{namespace:operation}}
        # It will not match simple variables like {{variable}}
        extension_pattern = re.compile(r"\{\{([\w-]+):([\w-]+)(?::(.*?))?\}\}")
        
        # Use a function for replacement to handle multiple matches correctly
        def replace_extension(match):
            namespace, operation, args_str = match.groups()
            extension_key = f"{namespace}:{operation}"

            if extension_key not in self.extension_functions:
                raise UnknownExtensionError(namespace, operation)

            func = self.extension_functions[extension_key]
            
            parsed_args: Dict[str, str] = {}
            if args_str:
                # Split arguments by comma, then by equals
                args_list = args_str.split(',')
                for arg_pair in args_list:
                    if '=' in arg_pair:
                        key, val = arg_pair.split('=', 1)
                        parsed_args[key.strip()] = val.strip()
                    else:
                        # Handle cases where an arg might not have a value, though spec implies key=val
                        # For now, we'll assume valid key=val pairs as per problem description
                        pass # Or raise an error for malformed arguments

            # Call the extension function
            # Assuming function signature: func(arguments: Dict[str, str], dependencies: Dict[str, Any]) -> str
            try:
                return str(func(parsed_args, self.dependencies))
            except Exception as e:
                # Optionally, handle errors from extension functions more gracefully
                # For now, let them propagate or wrap them
                raise e # Re-raise the original error

        rendered_content = extension_pattern.sub(replace_extension, rendered_content)

        # Process simple variables next
        # Regex to find simple variables: {{variable_name}}
        # This regex needs to be careful not to match already processed (or parts of) extensions
        # A simple way is to ensure it only matches if there's no ':' inside the {{}}
        simple_var_pattern = re.compile(r"\{\{([^:}]+?)\}\}") # Matches {{variable}} but not {{ns:op...}}
        
        # Refined simple variable replacement using re.sub with a function
        def replace_simple_variable(match_obj):
            # The match_obj.group(1) is the content inside {{ }}, e.g. "variableName"
            var_name = match_obj.group(1).strip()
            if var_name not in variables:
                raise MissingVariableError(var_name)
            return str(variables[var_name])

        rendered_content = simple_var_pattern.sub(replace_simple_variable, rendered_content)
        
        return rendered_content
