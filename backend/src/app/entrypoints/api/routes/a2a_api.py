from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, ValidationError
from typing import Any, Dict

from app.service_layer.a2a_service import A2ACapabilityService, CapabilityMetadata, A2AHandlerService # A2AHandlerService imported from here
# Note: AIPatternExecutionService is not used for now as per refined instructions
# from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService


a2a_api_router = APIRouter()


@a2a_api_router.post("/execute/{capability_name}")
async def execute_capability(
    capability_name: str,
    request_data: Dict[str, Any] = Body(...), # Using Dict[str, Any] as per common FastAPI practice for generic JSON
    a2a_service: A2ACapabilityService = Depends(),
    handler_service: A2AHandlerService = Depends() # Using A2AHandlerService as per instructions
) -> Any: # Return type will be dynamic based on capability.output_schema
    """
    Executes a specified capability by validating input data, invoking the capability handler, and returning a response validated against the capability's output schema.
    
    Args:
        capability_name: The name of the capability to execute.
        request_data: The JSON payload to be validated against the capability's input schema.
    
    Raises:
        HTTPException: 
            - 404 if the capability is not found.
            - 500 if input or output schemas are missing, or if the handler returns an unexpected type.
            - 422 if input data fails validation or cannot be parsed.
            - 500 if the handler's response fails output schema validation or cannot be processed.
    
    Returns:
        The response from the capability handler, validated against the capability's output schema.
    """
    capability = a2a_service.get_capability(capability_name)
    if not capability:
        raise HTTPException(status_code=404, detail=f"Capability '{capability_name}' not found")

    if not capability.input_schema:
        raise HTTPException(status_code=500, detail=f"Input schema not defined for capability '{capability_name}'")
    
    if not capability.output_schema:
        raise HTTPException(status_code=500, detail=f"Output schema not defined for capability '{capability_name}'")

    try:
        parsed_request = capability.input_schema(**request_data)
    except ValidationError as e:
        # Pydantic's ValidationError provides detailed error messages
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e: # Catch any other parsing errors
        raise HTTPException(status_code=422, detail=f"Invalid request format for {capability_name}: {str(e)}")

    # Dispatch the request to the handler_service
    # The handler_service is expected to return a dictionary or a Pydantic model instance
    response_data = await handler_service.handle_a2a_request(
        capability_name=capability_name, 
        data=parsed_request
    )

    # Ensure response_data conforms to output_schema
    # If response_data is a dict, try to parse it with the output_schema
    # If it's already a BaseModel, Pydantic will validate it on assignment (if types are compatible)
    # or when model_validate is called.
    try:
        if isinstance(response_data, dict):
            # The tests expect the handler_service mock to return a dict like {'summary': 'Mocked summary'}
            # This will be parsed into the capability's output_schema.
            final_response = capability.output_schema(**response_data)
        elif isinstance(response_data, capability.output_schema):
            final_response = response_data # Already correct type
        else:
            # If the response_data is neither a dict nor an instance of the expected output_schema,
            # it's an unexpected type from the handler.
            raise HTTPException(status_code=500, detail=f"Handler for '{capability_name}' returned an unexpected data type.")
            
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Handler for '{capability_name}' returned data that does not match the output schema: {e.errors()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response from handler for '{capability_name}': {str(e)}")

    return final_response
