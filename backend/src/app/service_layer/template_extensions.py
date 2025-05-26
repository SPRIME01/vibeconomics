import json # Ensure json is imported at the top
from typing import Any, Dict
from app.adapters.mem0_adapter import Mem0Adapter, MemoryWriteRequest # Assuming Mem0Adapter and MemoryWriteRequest are available here
# If MemorySearchRequest and individual search result types are defined, they might be imported too.
# from app.adapters.mem0_adapter import MemorySearchRequest, SearchResultItem # Example

# Define specific exception for argument errors if desired, or use ValueError
class ExtensionArgumentError(ValueError):
    pass

def mem0_add_extension_function(arguments: Dict[str, str], dependencies: Dict[str, Any]) -> str:
    '''
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
    '''
    if 'mem0_adapter' not in dependencies:
        raise ExtensionArgumentError("Dependency 'mem0_adapter' not found.")
    
    mem0_adapter: Mem0Adapter = dependencies['mem0_adapter']

    user_id = arguments.get('user_id')
    text_content = arguments.get('text_content') # Changed from 'text' to 'text_content' to match issue description

    if not user_id:
        raise ExtensionArgumentError("Argument 'user_id' is required for mem0:add extension.")
    if not text_content:
        raise ExtensionArgumentError("Argument 'text_content' is required for mem0:add extension.")

    # Handle metadata if provided
    metadata_str = arguments.get('metadata')
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
        text_content=text_content, # Ensure this matches the field in MemoryWriteRequest
        metadata=metadata_dict
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


def mem0_search_extension_function(arguments: Dict[str, str], dependencies: Dict[str, Any]) -> str:
    '''
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
    '''
    if 'mem0_adapter' not in dependencies:
        raise ExtensionArgumentError("Dependency 'mem0_adapter' not found.")
    
    mem0_adapter: Mem0Adapter = dependencies['mem0_adapter']

    user_id = arguments.get('user_id')
    query = arguments.get('query')

    if not user_id:
        raise ExtensionArgumentError("Argument 'user_id' is required for mem0:search extension.")
    if not query:
        raise ExtensionArgumentError("Argument 'query' is required for mem0:search extension.")

    # Optional parameters
    limit = arguments.get('limit')
    min_score = arguments.get('min_score')

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
            min_score=min_score_float
            # If adapter expects a Pydantic model, construct it here:
            # search_request = MemorySearchRequest(user_id=user_id, query=query, limit=limit_int, min_score=min_score_float)
            # results = mem0_adapter.search(search_request)
        )
        
        if search_results:
            # Assuming search_results is a list of objects that can be serialized to JSON.
            # If they are Pydantic models, they might have a .dict() or .model_dump() method.
            # For simplicity, directly try to dump; adjust if models need specific serialization.
            try:
                return json.dumps([res.dict() if hasattr(res, 'dict') else res for res in search_results])
            except TypeError as te:
                # Fallback or more specific serialization if needed
                print(f"Error serializing search results to JSON: {te}")
                # Attempt a simpler serialization if complex objects fail
                try:
                    return json.dumps([str(res) for res in search_results])
                except Exception:
                    return "[]" # Return empty JSON array on secondary failure
        else:
            return "[]" # Return empty JSON array if no results
    except Exception as e:
        # Log the exception e
        print(f"Error calling mem0_adapter.search: {e}") # Or use proper logging
        return "[]" # Return empty JSON array on error
