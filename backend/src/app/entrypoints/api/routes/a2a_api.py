from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import ValidationError

from app.entrypoints.api.dependencies import (
    get_a2a_capability_service,
    get_a2a_handler_service,
)
from app.service_layer.a2a_service import A2ACapabilityService, A2AHandlerService

a2a_api_router = APIRouter()


@a2a_api_router.post("/execute/{capability_name}")
async def execute_capability(
    capability_name: str,
    request_data: dict[str, Any] = Body(...),
    a2a_service: A2ACapabilityService = Depends(get_a2a_capability_service),
    handler_service: A2AHandlerService = Depends(get_a2a_handler_service),
) -> Any:
    """
    Executes a specified capability by validating input data, invoking the handler, and returning a validated response.

    Validates the incoming request against the capability's input schema, dispatches the request to the handler service, and ensures the handler's response conforms to the capability's output schema. Returns the validated response or raises appropriate HTTP errors for missing schemas, validation failures, or unexpected handler results.

    Args:
        capability_name: The name of the capability to execute.
        request_data: The JSON payload to be validated against the capability's input schema.

    Returns:
        The validated response matching the capability's output schema.

    Raises:
        HTTPException: If the capability is not found, schemas are missing, input or output validation fails, or the handler returns an unexpected result.
    """
    capability = a2a_service.get_capability(capability_name)
    if not capability:
        raise HTTPException(
            status_code=404, detail=f"Capability '{capability_name}' not found"
        )

    if not capability.input_schema:
        raise HTTPException(
            status_code=500,
            detail=f"Input schema not defined for capability '{capability_name}'",
        )

    if not capability.output_schema:
        raise HTTPException(
            status_code=500,
            detail=f"Output schema not defined for capability '{capability_name}'",
        )

    try:
        parsed_request = capability.input_schema(**request_data)
    except ValidationError as e:
        # Pydantic's ValidationError provides detailed error messages
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:  # Catch any other parsing errors
        raise HTTPException(
            status_code=422,
            detail=f"Invalid request format for {capability_name}: {str(e)}",
        )

    # Dispatch the request to the handler_service
    # The handler_service is expected to return a dictionary or a Pydantic model instance
    response_data = await handler_service.handle_a2a_request(
        capability_name=capability_name, data=parsed_request
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
            final_response = response_data  # Already correct type
        else:
            # If the response_data is neither a dict nor an instance of the expected output_schema,
            # it's an unexpected type from the handler.
            raise HTTPException(
                status_code=500,
                detail=f"Handler for '{capability_name}' returned an unexpected data type.",
            )

    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Handler for '{capability_name}' returned data that does not match the output schema: {e.errors()}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing response from handler for '{capability_name}': {str(e)}",
        )

    return final_response
