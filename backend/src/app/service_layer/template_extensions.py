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
        Initializes the TemplateExtensionRegistry with an empty registry for extension functions.
        """
        self._extensions: dict[str, Callable[..., Any]] = {} # Allow async callables returning Any (e.g. dict or str)

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """
        Registers a template extension function under the specified name.
        
        The function can be synchronous or asynchronous and will be available for template processing via this registry.
        
        Args:
            name: The unique name to associate with the extension function.
            func: The extension function to register.
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
        Returns a dictionary of all registered template extension functions.
        
        Each key is the extension name, and each value is the corresponding callable.
        """
        return self._extensions.copy() # Corrected from self.list_extensions()

    def _find_extension_boundaries(
        self, template: str
    ) -> list[tuple[int, int, str, str, str]]:
        """
        Parses the template string to locate all extension calls and their boundaries.
        
        Returns:
            A list of tuples, each containing the start and end positions of the extension in the template, the namespace, operation, and argument string for each extension found.
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
        Processes and replaces all template extension calls in the input string with their evaluated results.
        
        Scans the template for extension calls in the format `{{namespace:operation:args}}`, parses arguments according to the extension type, and invokes the corresponding registered extension functions (supporting both synchronous and asynchronous functions). If an extension function returns a tuple `(actual_result, output_var_name)`, the result is stored in the `variables` dictionary under the specified name and the extension is replaced with an empty string. Otherwise, the extension is replaced with the function's result, serialized to JSON if it is a dictionary or list.
        
        Args:
            template: The template string containing extension calls.
            variables: A dictionary for storing variables produced by extension functions.
        
        Returns:
            The template string with all extensions replaced by their evaluated results.
        """
        processed_template = template

        # Process extensions from right to left to maintain positions
        extensions = self._find_extension_boundaries(template)

        for start_pos, end_pos, namespace, operation, args_str in reversed(extensions):
            extension_name = f"{namespace}_{operation}"
            full_match_str = template[start_pos:end_pos]
            replacement_text = full_match_str # Default to original tag if not found or error occurs (error part removed)

            if extension_name in self._extensions:
                # Removed the try...except Exception as e block here
                # Exceptions from extension_function will now propagate
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
                        returned_value = await extension_function(*args)
                    else:
                        returned_value = extension_function(*args)
                    
                    # Check for the new tuple format (actual_result, output_var_name)
                    if isinstance(returned_value, tuple) and len(returned_value) == 2:
                        actual_result, output_var_name = returned_value
                        if output_var_name and isinstance(output_var_name, str):
                            variables[output_var_name] = actual_result # Store result in variables
                            replacement_text = "" # Replace with empty string in template
                        else: # output_var_name is None or invalid, treat actual_result as the direct replacement
                            if isinstance(actual_result, dict) or isinstance(actual_result, list):
                                replacement_text = json.dumps(actual_result)
                            else:
                                replacement_text = str(actual_result)
                    else: # Standard return type (not a special tuple)
                        if isinstance(returned_value, dict) or isinstance(returned_value, list):
                            replacement_text = json.dumps(returned_value)
                        else:
                            replacement_text = str(returned_value)

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
        A dictionary containing extension functions for searching and adding memories, suitable for use in template processing.
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
    Creates A2A template extensions for invoking remote agent capabilities asynchronously.
    
    Returns:
        A dictionary containing the asynchronous 'a2a_invoke' extension function. This function parses a colon-separated argument string to extract required parameters ('agent_url', 'capability'), an optional JSON 'payload', and an optional 'output_variable' name. It then calls the provided A2AClientAdapter to execute the remote capability and returns a tuple of the response data and the output variable name (if specified).
    
    Raises:
        ExtensionArgumentError: If required arguments are missing or the payload is invalid JSON.
        RuntimeError: If the adapter is not available.
    """
    async def _a2a_invoke_extension_async(gpt_args_str: str) -> tuple[dict, str | None]:
        """
        Invokes a remote capability on an A2A agent using parsed arguments.
        
        Parses a colon-separated string of key-value pairs to extract the agent URL, capability name, optional JSON payload, and an optional output variable name. Executes the specified capability asynchronously via the A2A adapter and returns the response data along with the output variable name if provided.
        
        Args:
            gpt_args_str: Colon-separated key=value pairs specifying 'agent_url', 'capability', optional 'payload' (as a JSON string), and optional 'output_variable'.
        
        Returns:
            A tuple containing the response data dictionary from the remote capability invocation and the output variable name if specified, otherwise None.
        
        Raises:
            ExtensionArgumentError: If required arguments are missing or the payload is not valid JSON.
            RuntimeError: If the A2A adapter is not available.
        """
        parsed_args = {}
        # More robust parsing for key=value pairs separated by ':'
        # Handles cases where values might contain colons (e.g., in JSON payload)
        # by splitting only at colons that are part of the key=value structure, not within JSON values.
        # A simple split(':') is not robust enough if payload contains colons.
        # This regex-based approach is more robust for "key=value" pairs separated by colons.
        import re
        # Regex to find key=value pairs, allowing for colons within the value part if it's quoted or part of JSON
        # This is still a simplification. A truly robust parser for this syntax would be more complex.
        # For now, we assume keys do not contain '=' and values are what's after the first '='.
        # The main split is by ':', but we must be careful not to split inside a JSON payload.
        # Let's parse output_variable first, then the rest.
        
        temp_args_str = gpt_args_str
        output_var_name: str | None = None

        # Look for output_variable explicitly
        output_var_marker = "output_variable="
        if output_var_marker in temp_args_str:
            # Split by output_variable to isolate it
            parts_around_output_var = temp_args_str.split(output_var_marker, 1)
            if len(parts_around_output_var) > 1:
                # Potential output_var_name and the rest of its value string
                potential_output_var_value_part = parts_around_output_var[1]
                # The output_var_name is until the next colon (if any) that separates it from other args
                next_colon_idx = potential_output_var_value_part.find(':')
                if next_colon_idx != -1:
                    output_var_name = potential_output_var_value_part[:next_colon_idx].strip()
                    # Reconstruct temp_args_str without the output_variable part for further parsing
                    remaining_after_output_var = potential_output_var_value_part[next_colon_idx:]
                    temp_args_str = (parts_around_output_var[0].strip(':') + remaining_after_output_var).strip(':')
                else: # output_variable is the last argument
                    output_var_name = potential_output_var_value_part.strip()
                    temp_args_str = parts_around_output_var[0].strip(':')
        
        # Parse the remaining arguments (agent_url, capability, payload)
        arg_components = temp_args_str.split(':')
        current_key = None
        current_value_parts: list[str] = []

        for component in arg_components:
            if '=' in component: # New key=value pair
                if current_key is not None and current_value_parts: # Save previous accumulated value
                    parsed_args[current_key] = ':'.join(current_value_parts).strip()
                
                key, value_part = component.split('=', 1)
                current_key = key.strip()
                current_value_parts = [value_part]
            elif current_key is not None: # Continuation of the previous value (e.g. colon in JSON)
                current_value_parts.append(component)
        
        if current_key is not None and current_value_parts: # Save the last argument
             parsed_args[current_key] = ':'.join(current_value_parts).strip()

        agent_url = parsed_args.get("agent_url")
        capability_name = parsed_args.get("capability")
        payload_str = parsed_args.get("payload", "{}") # Default to empty JSON string

        if not agent_url:
            raise ExtensionArgumentError("Missing 'agent_url' in a2a:invoke arguments.")
        if not capability_name:
            raise ExtensionArgumentError("Missing 'capability' in a2a:invoke arguments.")

        try:
            payload_dict = json.loads(payload_str)
        except json.JSONDecodeError as e:
            raise ExtensionArgumentError(f"Invalid JSON payload in a2a:invoke for key 'payload': {e}. Payload string was: {payload_str}")

        request_payload_model = GenericRequestData(**payload_dict)

        if not adapter:
            raise RuntimeError("A2AClientAdapter not available for a2a:invoke extension.")

        response_data = await adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload_model,
            response_model=None  # We want a dict back
        )
        return response_data, output_var_name

    return {
        "a2a_invoke": _a2a_invoke_extension_async, # type: ignore[dict-item]
    }


def create_activepieces_extensions(
    activepieces_adapter: AbstractActivePiecesAdapter,
) -> dict[str, Callable[..., str]]:
    """
    Creates template extension functions for running ActivePieces workflows.
    
    Returns:
        A dictionary containing the 'activepieces_run_workflow' extension function, which executes a workflow using the provided ActivePieces adapter. The function accepts a workflow ID and input data as a JSON string, returning the workflow result as a JSON string or an error message if execution fails.
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
    
    Supports specific parsing for 'memory:search' (user_id and query) and 'activepieces:run_workflow' (workflow_id and input JSON). For other extensions, passes the remaining argument string as 'gpt_args_str' for further parsing by the extension itself.
    
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
