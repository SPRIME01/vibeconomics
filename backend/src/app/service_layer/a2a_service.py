from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class CapabilityMetadata:
    """Metadata for an Agent-to-Agent capability."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: type[BaseModel] | None = None,
        output_schema: type[BaseModel] | None = None,
        handler: Callable | None = None,
    ):
        """Initialize capability metadata."""
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.handler = handler


class A2ACapabilityService:
    """Service for managing Agent-to-Agent capabilities."""

    def __init__(self):
        """Initialize the A2A capability service."""
        self._capabilities: dict[str, CapabilityMetadata] = {}

    def get_capability(self, capability_name: str) -> CapabilityMetadata | None:
        """Get a capability by name."""
        return self._capabilities.get(capability_name)

    def register_capability(self, capability: CapabilityMetadata) -> None:
        """Register a new capability."""
        self._capabilities[capability.name] = capability

    def list_capabilities(self) -> list[CapabilityMetadata]:
        """List all registered capabilities."""
        return list(self._capabilities.values())


class A2AHandlerService:
    """Service for handling Agent-to-Agent requests."""

    def __init__(self):
        """Initialize the A2A handler service."""
        pass

    async def handle_a2a_request(
        self, capability_name: str, data: BaseModel
    ) -> dict[str, Any] | BaseModel:
        """Handle an A2A request for a specific capability."""
        # This is a stub implementation that returns mock data for testing
        # In a real implementation, this would route to specific handlers
        # based on the capability_name

        # For testing purposes, return a basic response
        if hasattr(data, "message"):
            return {"summary": f"Processed: {data.message}"}
        elif hasattr(data, "input_text"):
            return {"output_text": f"Processed: {data.input_text}"}
        else:
            return {"result": "Generic response"}
