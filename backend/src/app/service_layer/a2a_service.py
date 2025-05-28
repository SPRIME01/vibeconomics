from pydantic import BaseModel
from typing import Dict, Type, Any, List
from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse


class CapabilityMetadata(BaseModel):
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    handler: Any  # Initially None or a placeholder

    class Config:
        arbitrary_types_allowed = True


class A2ACapabilityService:
    def __init__(self):
        """
        Initializes the capability service with an empty registry.
        """
        self.capabilities: Dict[str, CapabilityMetadata] = {}

    def register_capability(self, capability_metadata: CapabilityMetadata):
        """
        Registers a new capability with the service.
        
        Raises:
            ValueError: If a capability with the same name is already registered.
        """
        if capability_metadata.name in self.capabilities:
            raise ValueError(
                f"Capability '{capability_metadata.name}' already registered – "
                "choose a unique name or call `update_capability` explicitly."
            )
        self.capabilities[capability_metadata.name] = capability_metadata
    def get_capability(self, capability_name: str) -> CapabilityMetadata | None:
        """
        Retrieves the metadata for a registered capability by its name.
        
        Args:
            capability_name: The unique name of the capability to retrieve.
        
        Returns:
            The CapabilityMetadata instance if found, or None if the capability is not registered.
        """
        return self.capabilities.get(capability_name)

    def list_capabilities(self) -> List[CapabilityMetadata]:
        """
        Returns a list of all registered capability metadata objects.
        """
        return list(self.capabilities.values())


class A2AHandlerService:
    """
    Placeholder service for handling A2A requests.
    The actual implementation of this service is not part of this subtask.
    This service will be responsible for dispatching the request to the
    appropriate handler based on the capability name.
    """
    async def handle_a2a_request(self, capability_name: str, data: BaseModel) -> Any:
        # In a real implementation, this method would look up the capability
        # and execute its associated handler.
        # For the "SummarizeText" capability, it might call a summarization function.
        # The tests expect this to return a dict for "SummarizeText"
        # e.g., {'summary': 'Mocked summary'}
        """
        Processes an A2A request by dispatching it to the appropriate capability handler.
        
        Args:
            capability_name: The name of the capability to invoke.
            data: Input data conforming to the capability's input schema.
        
        Returns:
            The result produced by the capability's handler, such as a dictionary for certain capabilities.
        """
        pass

    class Config:
        arbitrary_types_allowed = True
