import httpx
from pydantic import BaseModel, ValidationError
from typing import Type
import json # For JSONDecodeError


class A2AClientAdapter:
    """
    Adapter for making Agent-to-Agent (A2A) calls to remote capabilities.
    """
    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initializes the A2AClientAdapter with an asynchronous HTTP client.
        
        Args:
            http_client: The asynchronous HTTP client used for making agent-to-agent requests.
        """
        self.http_client = http_client

    async def execute_remote_capability(
        self,
        agent_url: str,
        capability_name: str,
        request_payload: BaseModel,
        response_model: Type[BaseModel] | None = None, # Made optional
    ) -> BaseModel | dict: # Return type updated
        """
        Executes a remote capability on another agent via an asynchronous HTTP POST request.
        
        Sends a JSON-serialized request payload to the specified agent and capability endpoint. If a response model is provided, the response is deserialized into that Pydantic model; otherwise, the raw JSON dictionary is returned.
        
        Args:
            agent_url: The base URL of the target agent.
            capability_name: The name of the capability to execute.
            request_payload: The Pydantic model instance representing the request payload.
            response_model: Optional Pydantic model type to deserialize the response into.
        
        Returns:
            An instance of the response_model if provided, otherwise a dictionary containing the response data.
        
        Raises:
            httpx.HTTPStatusError: If the remote server returns an HTTP error status.
            httpx.NetworkError: If a network error occurs.
            ValidationError: If the response cannot be validated against the response_model.
            RuntimeError: For JSON decoding failures or other unexpected errors.
        """
        url = f"{agent_url.rstrip('/')}/a2a/execute/{capability_name}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            response = await self.http_client.post(
                url,
                # .model_dump() is preferred over .dict() in Pydantic v2
                json=request_payload.model_dump(), 
                headers=headers
            )
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            response_data = response.json()
            
            if response_model:
                return response_model(**response_data)
            else:
                return response_data # Return raw dict if no model is provided

        except httpx.HTTPStatusError as e:
            # Re-raise specific HTTP errors to be handled by the caller
            # Optionally, log the error or add more context
            raise e
        
        except httpx.NetworkError as e:
            # Re-raise network errors
            # Optionally, log the error or add more context
            raise e
        
        except json.JSONDecodeError as e:
            # Handle cases where response.json() fails (e.g., empty or invalid JSON)
            # This can happen before Pydantic validation if the response isn't valid JSON.
            raise RuntimeError(f"Failed to decode JSON response from {url}: {e}") from e

        except ValidationError as e:
            # Re-raise Pydantic validation errors if response_data doesn't match response_model
            # This is only relevant if response_model is not None.
            if response_model:
                raise e
            # If response_model is None, ValidationError should not occur here from the parsing step.
            # Any other unexpected ValidationError might indicate a deeper issue, but this specific catch
            # for the None case seems unnecessary based on the logic flow.

        
        except Exception as e:
            # Catch any other unexpected errors during the process
            # This is a general fallback.
            # Consider if more specific error handling is needed for other httpx exceptions.
            raise RuntimeError(f"An unexpected error occurred when calling {url}: {e}") from e
