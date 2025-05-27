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
        self.capabilities: Dict[str, CapabilityMetadata] = {}

    def register_capability(self, capability_metadata: CapabilityMetadata):
        self.capabilities[capability_metadata.name] = capability_metadata

    def get_capability(self, capability_name: str) -> CapabilityMetadata | None:
        return self.capabilities.get(capability_name)

    def list_capabilities(self) -> List[CapabilityMetadata]:
        return list(self.capabilities.values())


class A2AHandlerService(BaseModel): # Or just a regular class if no Pydantic features needed for the service itself
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
        pass

    class Config:
        arbitrary_types_allowed = True
