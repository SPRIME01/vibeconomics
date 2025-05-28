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
from app.adapters.a2a_client_adapter import A2AClientAdapter # Import A2AClientAdapter
from pydantic import BaseModel, ConfigDict # For GenericRequest in a2a extension
from typing import Dict # For GenericRequest


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
        """
        Initializes the extension registry with an empty set of registered extensions.
        """
        self._extensions: dict[str, Callable[..., Any]] = {} # Allow async callables returning Any (e.g. dict or str)

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """
        Registers a template extension function under the specified name.
        
        The function can be synchronous or asynchronous and will be available for use in template processing.
        """
        self._extensions[name] = func

    def get(self, name: str) -> Callable[..., Any] | None:
        """
        Retrieves a registered extension function by name.
        
        Args:
            name: The name of the extension function to retrieve.
        
        Returns:
            The registered extension function if found, otherwise None.
        """
        return self._extensions.get(name)

    def list_extensions(self) -> dict[str, Callable[..., Any]]:
        """
        Returns a copy of the dictionary containing all registered template extension functions.
        
        Returns:
            A dictionary mapping extension names to their corresponding callables.
        """
        return self._extensions.copy() # Corrected from self.list_extensions()

    def _find_extension_boundaries(
        self, template: str
    ) -> list[tuple[int, int, str, str, str]]:
        """
        Identifies all template extension occurrences and their boundaries within the template string.
        
        Parses the template for extension patterns of the form `{{namespace:operation:args}}`, correctly handling nested braces and quoted strings within the arguments. Returns a list of tuples containing the start and end positions of each extension, along with the extracted namespace, operation, and argument string.
        
        Returns:
            A list of tuples, each containing (start_pos, end_pos, namespace, operation, args).
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
        """
        Processes all template extensions in the given template string asynchronously.
        
        Scans the template for extension patterns of the form `{{namespace:operation:args}}`, parses their arguments according to extension type, and replaces each extension with the result of its registered function. Supports both synchronous and asynchronous extension functions, converting non-string results to JSON strings. On error, inserts an error message in place of the extension.
        
        Args:
            template: The template string containing extension calls.
            variables: A dictionary of variables available for extension processing.
        
        Returns:
            The template string with all extensions replaced by their computed results.
        """
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
                    # Argument parsing logic needs to be robust and specific to each extension's needs.
                    # For a2a:invoke, the args_str itself is complex.
                    # For other extensions, it might be simpler.
                    # This part of the code might need a more structured approach if many extensions have complex args.

                    # For now, pass args_str directly to the extension function if it's designed to parse it.
                    # Or, implement parsing here if a common pattern emerges.
                    # The existing simple parsing is kept for non-a2a extensions.
                    if extension_name == "a2a_invoke":
                        # The a2a_invoke extension will handle parsing of its specific args_str format
                        args = [args_str]
                    elif extension_name == "activepieces_run_workflow":
                        if ":" in args_str: # Expects workflow_id:json_input_string
                            workflow_id, input_data_str_from_template = args_str.split(":", 1)
                            args = [workflow_id.strip(), input_data_str_from_template.strip()]
                        else: # Assume only workflow_id is passed, and input is empty JSON
                            args = [args_str.strip(), "{}"]
                    elif extension_name == "memory_search": # Expects user_id:query
                        if ":" in args_str:
                            user_id, query_from_template = args_str.split(":", 1)
                            args = [user_id.strip(), query_from_template.strip()]
                        else: # This case might be an error for memory_search or needs specific handling
                            args = [args_str.strip()] 
                    else:
                        args = [args_str.strip()] if args_str else []
                    
                    import inspect # To check if function is async
                    if inspect.iscoroutinefunction(extension_function):
                        replacement_value = await extension_function(*args)
                    else:
                        replacement_value = extension_function(*args)
                    
                    # Ensure replacement_text is a string
                    if isinstance(replacement_value, dict) or isinstance(replacement_value, list):
                        replacement_text = json.dumps(replacement_value)
                    else:
                        replacement_text = str(replacement_value)

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
    Creates memory-related template extension functions bound to the provided memory service.
    
    Returns:
        A dictionary mapping extension names to functions for searching and adding memories.
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


# --- A2A Extension ---
class GenericRequestData(BaseModel):
    model_config = ConfigDict(extra='allow')


def create_a2a_extensions(adapter: A2AClientAdapter) -> dict[str, Callable[..., Any]]:
    """
    Creates A2A-related template extensions bound to the provided A2AClientAdapter.
    
    Returns:
        A dictionary mapping extension names to their corresponding callable functions, including an asynchronous extension for invoking remote agent capabilities via the adapter.
    """
    async def _a2a_invoke_extension_async(gpt_args_str: str) -> dict:
        """
        Invokes a remote agent-to-agent (A2A) capability using parsed template arguments.
        
        Parses a colon-separated argument string to extract the agent URL, capability name, and a JSON payload. Validates required fields and deserializes the payload. Calls the associated A2A client adapter asynchronously to execute the remote capability and returns the response as a dictionary.
        
        Raises:
            ExtensionArgumentError: If required arguments are missing or the payload is not valid JSON.
            RuntimeError: If the A2A client adapter is not available.
        
        Returns:
            dict: The response data from the remote capability invocation.
        """
        agent_url = ""
        capability_name = ""
        payload_str = "{}" # Default to empty JSON

        # Basic parsing for key=value pairs separated by ':'
        # This parsing is simplistic and assumes clean input.
        # A more robust parser might be needed for complex cases or error handling.
        parts = gpt_args_str.split(':')
        parsed_args = {}
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                parsed_args[key.strip()] = value.strip()
        
        agent_url = parsed_args.get("agent_url")
        capability_name = parsed_args.get("capability")
        payload_str = parsed_args.get("payload", "{}")

        if not agent_url:
            raise ExtensionArgumentError("Missing 'agent_url' in a2a:invoke arguments.")
        if not capability_name:
            raise ExtensionArgumentError("Missing 'capability' in a2a:invoke arguments.")

        try:
            payload_dict = json.loads(payload_str)
        except json.JSONDecodeError as e:
            raise ExtensionArgumentError(f"Invalid JSON payload in a2a:invoke: {e}")

        # Wrap the payload_dict in a generic Pydantic model if needed by the adapter,
        # or pass dict directly if adapter supports it.
        # Current A2AClientAdapter expects a BaseModel for request_payload.
        # We use a generic model that allows any extra fields.
        request_payload_model = GenericRequestData(**payload_dict)

        if not adapter: # Should be provided via create_a2a_extensions closure
            raise RuntimeError("A2AClientAdapter not available for a2a:invoke extension.")

        response_data = await adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload_model,
            response_model=None  # We want a dict back
        )
        return response_data # This will be a dict

    return {
        "a2a_invoke": _a2a_invoke_extension_async,
    }


def create_activepieces_extensions(
    activepieces_adapter: AbstractActivePiecesAdapter,
) -> dict[str, Callable[..., str]]:
    """
    Creates template extension functions for running ActivePieces workflows.
    
    Returns:
        A dictionary mapping extension names to functions that execute workflows using the provided ActivePieces adapter. The main extension, `activepieces_run_workflow`, accepts a workflow ID and a JSON string of input data, runs the workflow, and returns the result as a JSON string. Errors in input parsing or workflow execution are returned as JSON error objects.
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
    Parses an extension call string into its extension name and argument dictionary.
    
    Supports specific parsing for 'memory:search' (user ID and query) and 'activepieces:run_workflow' (workflow ID and input JSON). For other extensions, returns the raw argument string under the key 'gpt_args_str'.
    
    Args:
        extension_text: The extension call string, e.g., 'memory:search:user123:my query'.
    
    Returns:
        A tuple containing the extension name (e.g., 'memory:search') and a dictionary of parsed arguments.
    
    Raises:
        ValueError: If the extension syntax is invalid or required arguments are missing.
    """
    # Only split on the first two colons; everything after is a single argument
    parts = extension_text.split(":", 2)

    if len(parts) < 3:
        raise ValueError(f"Invalid extension syntax: {extension_text}")

    namespace = parts[0]
    operation = parts[1]
    args_part = parts[2]

    extension_name = f"{namespace}:{operation}" # e.g. "memory:search"

    # This parser is specific to how memory:search was designed (user_id:query)
    # and how activepieces:run_workflow was designed (workflow_id:json_payload)
    # For a2a:invoke, the args_part itself is "key=value:key=value..."
    # The a2a_invoke extension function handles its own internal parsing of args_part.
    
    # The current TemplateExtensionRegistry.process_template_extensions
    # already has specific parsing logic for activepieces_run_workflow and memory_search.
    # For a2a_invoke, it will pass the raw args_str.
    # This function, parse_extension_call, seems to be unused by the main registry logic.
    # If it were to be used, it would need to be more generic or accommodate different arg styles.

    # For memory:search, expect format: user_id:query
    if extension_name == "memory:search":
        # Only split the args_part on the first colon
        arg_parts = args_part.split(":", 1)
        if len(arg_parts) != 2:
            raise ValueError(
                f"memory:search expects format 'user_id:query', got: {args_part}"
            )

        return extension_name, {"user_id": arg_parts[0], "query": arg_parts[1]}
    
    elif extension_name == "activepieces:run_workflow":
        arg_parts = args_part.split(":", 1)
        if len(arg_parts) == 2:
            return extension_name, {"workflow_id": arg_parts[0], "input_data_str": arg_parts[1]}
        else: # Only workflow_id provided
            return extension_name, {"workflow_id": arg_parts[0], "input_data_str": "{}"}

    # For other extensions (like a2a:invoke), pass the args_part as a single string.
    # The extension itself will parse this string.
    return extension_name, {"gpt_args_str": args_part} # Changed key to 'gpt_args_str' for clarity
