import json  # Ensure json is imported at the top
from collections.abc import Callable
from typing import Any

from app.adapters.activepieces_adapter import (
    AbstractActivePiecesAdapter,  # Changed import for consistency
)
from app.adapters.mem0_adapter import (  # Assuming Mem0Adapter and MemoryWriteRequest are available here
    Mem0Adapter,
    MemoryWriteRequest,
)
from app.service_layer.memory_service import AbstractMemoryService


# Define specific exception for argument errors if desired, or use ValueError
class ExtensionArgumentError(ValueError):
    pass


def mem0_add_extension_function(
    arguments: dict[str, str], dependencies: dict[str, Any]
) -> str:
    """
    Adds memory to Mem0 using the Mem0Adapter.

    Args:
        arguments: A dictionary of arguments parsed from the template.
                   Expected keys: 'user_id', 'text_content'.
                   Optional keys: 'metadata' (as a JSON string if provided).
        dependencies: A dictionary of dependencies.
                      Expected key: 'mem0_adapter' (an instance of Mem0Adapter).

    Returns:
        The memory ID returned by mem0_adapter.add, or an empty string if an error occurs
        or if the adapter returns None/empty.

    Raises:
        ExtensionArgumentError: If required arguments ('user_id', 'text_content') are missing
                                or if 'mem0_adapter' is not found in dependencies.
        JSONDecodeError: If 'metadata' is provided but is not valid JSON.
    """
    if "mem0_adapter" not in dependencies:
        raise ExtensionArgumentError("Dependency 'mem0_adapter' not found.")

    mem0_adapter: Mem0Adapter = dependencies["mem0_adapter"]

    user_id = arguments.get("user_id")
    text_content = arguments.get(
        "text_content"
    )  # Changed from 'text' to 'text_content' to match issue description

    if not user_id:
        raise ExtensionArgumentError(
            "Argument 'user_id' is required for mem0:add extension."
        )
    if not text_content:
        raise ExtensionArgumentError(
            "Argument 'text_content' is required for mem0:add extension."
        )

    # Handle metadata if provided
    metadata_str = arguments.get("metadata")
    metadata_dict = None
    if metadata_str:
        # import json # Moved to top
        try:
            metadata_dict = json.loads(metadata_str)
        except json.JSONDecodeError as e:
            # Raising ExtensionArgumentError for consistency in function's error reporting
            raise ExtensionArgumentError(f"Invalid JSON in 'metadata' argument: {e}")

    write_request = MemoryWriteRequest(
        user_id=user_id,
        text_content=text_content,  # Ensure this matches the field in MemoryWriteRequest
        metadata=metadata_dict,
    )

    try:
        memory_id = mem0_adapter.add(write_request)
        return memory_id if memory_id is not None else ""
    except Exception as e:
        # Log the exception e with traceback
        # Consider how to report errors; returning empty string for now
        # Use proper logging instead of print
        import logging

        logging.exception(f"Error calling mem0_adapter.add: {e}")
        return ""


def mem0_search_extension_function(
    arguments: dict[str, str], dependencies: dict[str, Any]
) -> str:
    """
    Searches memories in Mem0 using the Mem0Adapter.

    Args:
        arguments: A dictionary of arguments parsed from the template.
                   Expected keys: 'user_id', 'query'.
                   Optional keys: 'limit' (int), 'min_score' (float).
        dependencies: A dictionary of dependencies.
                      Expected key: 'mem0_adapter' (an instance of Mem0Adapter).

    Returns:
        A JSON string representation of the search results,
        or an empty string if an error occurs or no results are found.

    Raises:
        ExtensionArgumentError: If required arguments ('user_id', 'query') are missing
                                or if 'mem0_adapter' is not found in dependencies.
    """
    if "mem0_adapter" not in dependencies:
        raise ExtensionArgumentError("Dependency 'mem0_adapter' not found.")

    mem0_adapter: Mem0Adapter = dependencies["mem0_adapter"]

    user_id = arguments.get("user_id")
    query = arguments.get("query")

    if not user_id:
        raise ExtensionArgumentError(
            "Argument 'user_id' is required for mem0:search extension."
        )
    if not query:
        raise ExtensionArgumentError(
            "Argument 'query' is required for mem0:search extension."
        )

    # Optional parameters
    limit = arguments.get("limit")
    min_score = arguments.get("min_score")

    limit_int = None
    if limit is not None:
        try:
            limit_int = int(limit)
        except ValueError:
            raise ExtensionArgumentError("Argument 'limit' must be an integer.")

    min_score_float = None
    if min_score is not None:
        try:
            min_score_float = float(min_score)
        except ValueError:
            raise ExtensionArgumentError("Argument 'min_score' must be a float.")

    try:
        # Assuming mem0_adapter.search takes these parameters.
        # Adjust if the adapter's search method has a different signature,
        # e.g., if it expects a SearchRequest object.
        search_results = mem0_adapter.search(
            user_id=user_id,
            query=query,
            limit=limit_int,
            min_score=min_score_float,
            # If adapter expects a Pydantic model, construct it here:
            # search_request = MemorySearchRequest(user_id=user_id, query=query, limit=limit_int, min_score=min_score_float)
            # results = mem0_adapter.search(search_request)
        )

        if search_results:
            # Assuming search_results is a list of objects that can be serialized to JSON.
            # If they are Pydantic models, they might have a .dict() or .model_dump() method.
            # For simplicity, directly try to dump; adjust if models need specific serialization.
            try:
                return json.dumps(
                    [
                        res.dict() if hasattr(res, "dict") else res
                        for res in search_results
                    ]
                )
            except TypeError as te:
                # Fallback or more specific serialization if needed
                print(f"Error serializing search results to JSON: {te}")
                # Attempt a simpler serialization if complex objects fail
                try:
                    return json.dumps([str(res) for res in search_results])
                except Exception:
                    return "[]"  # Return empty JSON array on secondary failure
        else:
            return "[]"  # Return empty JSON array if no results
    except Exception as e:
        # Log the exception e with traceback
        # Use proper logging instead of print
        import logging

        logging.exception(f"Error calling mem0_adapter.search: {e}")
        return "[]"  # Return empty JSON array on error


def activepieces_run_workflow(
    activepieces_adapter: AbstractActivePiecesAdapter,
    workflow_id: str,
    input_data_str: str,
) -> str:
    """
    Runs an ActivePieces workflow and returns the result as a JSON string.

    Args:
        activepieces_adapter: An instance of AbstractActivePiecesAdapter.
        workflow_id: The ID of the workflow to run.
        input_data_str: A JSON string representing the input data for the workflow.

    Returns:
        A JSON string representing the result of the workflow execution,
        or a JSON string with an error message if an error occurs.
    """
    try:
        # Trim whitespace and ensure we have at least empty JSON
        input_data_str = input_data_str.strip() or "{}"
        parsed_input_data: dict[str, Any] = json.loads(input_data_str)
    except json.JSONDecodeError as e:
        return json.dumps({"success": False, "error": f"Invalid JSON input: {e}"})

    # Catch adapter exceptions
    try:
        result = activepieces_adapter.run_workflow(
            workflow_id=workflow_id, input_data=parsed_input_data
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


class TemplateExtensionRegistry:
    """Registry for template extensions that can be called from templates."""

    def __init__(self) -> None:
        self._extensions: dict[str, Callable[..., str]] = {}

    def register(self, name: str, func: Callable[..., str]) -> None:
        """Register a template extension function."""
        self._extensions[name] = func

    def get(self, name: str) -> Callable[..., str] | None:
        """Get a registered extension function."""
        return self._extensions.get(name)

    def list_extensions(self) -> dict[str, Callable[..., str]]:
        """List all registered extensions."""
        return self._extensions.copy()

    def _find_extension_boundaries(
        self, template: str
    ) -> list[tuple[int, int, str, str, str]]:
        """
        Find all extension boundaries in the template.

        Returns:
            List of tuples: (start_pos, end_pos, namespace, operation, args)
        """
        extensions = []
        i = 0

        while i < len(template) - 1:
            # Look for opening {{
            if template[i : i + 2] == "{{":
                start_pos = i
                i += 2

                # Parse namespace (until first colon)
                namespace = ""
                while i < len(template) and template[i] not in ":}":
                    namespace += template[i]
                    i += 1

                if i >= len(template) or template[i] != ":":
                    i = start_pos + 1
                    continue

                i += 1  # Skip first colon

                # Parse operation (until second colon)
                operation = ""
                while i < len(template) and template[i] not in ":}":
                    operation += template[i]
                    i += 1

                if i >= len(template) or template[i] != ":":
                    i = start_pos + 1
                    continue

                i += 1  # Skip second colon

                # Parse arguments (until matching }))
                args = ""
                in_string = False
                escape_next = False
                brace_depth = 0  # Track nested braces inside JSON

                while i < len(template):
                    char = template[i]

                    # Check for end of extension first
                    if (
                        not in_string
                        and i + 1 < len(template)
                        and template[i : i + 2] == "}}"
                        and brace_depth == 0
                    ):
                        # Found the end of extension
                        i += 2  # Skip both closing braces
                        break

                    if escape_next:
                        args += char
                        escape_next = False
                    elif char == "\\" and in_string:
                        args += char
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                        args += char
                    elif char == "{" and not in_string:
                        brace_depth += 1
                        args += char
                    elif char == "}" and not in_string:
                        brace_depth -= 1
                        args += char
                    else:
                        args += char

                    i += 1

                # Check if we found a complete extension
                if i <= len(template) and args:
                    # Found complete extension
                    extensions.append(
                        (
                            start_pos,
                            i,
                            namespace.strip(),
                            operation.strip(),
                            args.strip(),
                        )
                    )
                else:
                    # Malformed extension, continue from start + 1
                    i = start_pos + 1
            else:
                i += 1

        return extensions

    async def process_template_extensions(
        self, template: str, variables: dict[str, Any]
    ) -> str:
        """Process template extensions in the format {{namespace:operation:args}}."""
        processed_template = template

        # Process extensions from right to left to maintain positions
        extensions = self._find_extension_boundaries(template)

        for start_pos, end_pos, namespace, operation, args_str in reversed(extensions):
            extension_name = f"{namespace}_{operation}"
            full_match_str = template[start_pos:end_pos]
            replacement_text = full_match_str

            if extension_name in self._extensions:
                try:
                    extension_function = self._extensions[extension_name]

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

                    replacement_text = extension_function(*args)
                except Exception as e:
                    replacement_text = (
                        f"[ERROR IN EXTENSION: {extension_name} - {str(e)}]"
                    )

            # Replace this specific occurrence
            processed_template = (
                processed_template[:start_pos]
                + replacement_text
                + processed_template[end_pos:]
            )

        return processed_template


def memory_search_extension(
    memory_service: AbstractMemoryService, user_id: str, query: str, limit: int = 5
) -> str:
    """
    Template extension function for memory search.

    Args:
        memory_service: The memory service instance
        user_id: User ID to search memories for
        query: Search query
        limit: Maximum number of results to return

    Returns:
        Formatted string of search results
    """
    try:
        results = memory_service.search(user_id=user_id, query=query, limit=limit)

        if not results:
            return "No relevant memories found."

        formatted_results = []
        for i, result in enumerate(results, 1):
            # result is now a MemorySearchResult object
            content = result.content
            score = result.score
            formatted_results.append(f"{i}. {content} (relevance: {score:.2f})")

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Error searching memories: {str(e)}"


def create_memory_extensions(
    memory_service: AbstractMemoryService,
) -> dict[str, Callable[..., str]]:
    """
    Create memory-related template extensions bound to a memory service.

    Args:
        memory_service: The memory service instance to use

    Returns:
        Dictionary of extension functions
    """

    def bound_memory_search(user_id: str, query: str, limit: int = 5) -> str:
        return memory_search_extension(memory_service, user_id, query, limit)

    def memory_add(user_id: str, content: str, metadata: str = "{}") -> str:
        """Template extension for adding memories."""
        try:
            import json

            metadata_dict = json.loads(metadata) if metadata != "{}" else None
            memory_id = memory_service.add(
                user_id=user_id, content=content, metadata=metadata_dict
            )
            return (
                f"Memory stored with ID: {memory_id}"
                if memory_id
                else "Failed to store memory"
            )
        except Exception as e:
            return f"Error storing memory: {str(e)}"

    return {
        "memory_search": bound_memory_search,
        "memory_add": memory_add,
    }


def create_activepieces_extensions(
    activepieces_adapter: AbstractActivePiecesAdapter,
) -> dict[str, Callable[..., str]]:
    """
    Create ActivePieces-related template extensions bound to an ActivePieces adapter.

    Args:
        activepieces_adapter: The ActivePieces adapter instance to use.

    Returns:
        Dictionary of extension functions.
    """

    def bound_activepieces_run_workflow(workflow_id: str, input_data_str: str) -> str:
        """
        Bound version of activepieces_run_workflow that uses the provided adapter.
        """
        try:
            # Trim whitespace and ensure we have at least empty JSON
            input_data_str = input_data_str.strip() or "{}"
            parsed_input_data: dict[str, Any] = json.loads(input_data_str)
        except json.JSONDecodeError as e:
            return json.dumps({"success": False, "error": f"Invalid JSON input: {e}"})

        # Catch adapter exceptions
        try:
            result = activepieces_adapter.run_workflow(
                workflow_id=workflow_id, input_data=parsed_input_data
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    return {
        "activepieces_run_workflow": bound_activepieces_run_workflow,
        # This key will allow calling {{activepieces:run_workflow:...}}
        # because TemplateExtensionRegistry.process_template_extensions
        # combines namespace and operation with an underscore to look up the function.
    }


def parse_extension_call(extension_text: str) -> tuple[str, dict[str, Any]]:
    """
    Parse extension call syntax like 'memory:search:user123:my query'.

    Args:
        extension_text: The extension call text

    Returns:
        Tuple of (extension_name, kwargs)
    """
    # Only split on the first two colons; everything after is a single argument
    parts = extension_text.split(":", 2)

    if len(parts) < 3:
        raise ValueError(f"Invalid extension syntax: {extension_text}")

    namespace = parts[0]
    operation = parts[1]
    args_part = parts[2]

    extension_name = f"{namespace}:{operation}"

    # For memory:search, expect format: user_id:query
    if extension_name == "memory:search":
        # Only split the args_part on the first colon
        arg_parts = args_part.split(":", 1)
        if len(arg_parts) != 2:
            raise ValueError(
                f"memory:search expects format 'user_id:query', got: {args_part}"
            )

        return extension_name, {"user_id": arg_parts[0], "query": arg_parts[1]}

    # For other extensions, treat args_part as a single argument (e.g., JSON string)
    return extension_name, {"args": [args_part]}
