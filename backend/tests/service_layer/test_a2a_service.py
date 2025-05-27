import pytest
from pydantic import BaseModel
from typing import Any

from app.service_layer.a2a_service import A2ACapabilityService, CapabilityMetadata
from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse


@pytest.fixture
def a2a_capability_service() -> A2ACapabilityService:
    return A2ACapabilityService()


def test_register_and_get_capability(a2a_capability_service: A2ACapabilityService):
    capability_metadata = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None  # Placeholder for handler
    )
    a2a_capability_service.register_capability(capability_metadata)
    retrieved_capability = a2a_capability_service.get_capability("SummarizeText")

    assert retrieved_capability is not None
    assert retrieved_capability.name == "SummarizeText"
    assert retrieved_capability.description == "Summarizes a given text."
    assert retrieved_capability.input_schema == SummarizeTextA2ARequest
    assert retrieved_capability.output_schema == SummarizeTextA2AResponse


def test_get_nonexistent_capability(a2a_capability_service: A2ACapabilityService):
    retrieved_capability = a2a_capability_service.get_capability("NonExistentCapability")
    assert retrieved_capability is None


def test_list_capabilities(a2a_capability_service: A2ACapabilityService):
    capability1_metadata = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None
    )
    # Define a dummy model for a second capability for testing list_capabilities
    class AnotherRequest(BaseModel):
        data: str

    class AnotherResponse(BaseModel):
        result: str

    capability2_metadata = CapabilityMetadata(
        name="AnotherCapability",
        description="Another capability for testing.",
        input_schema=AnotherRequest,
        output_schema=AnotherResponse,
        handler=None
    )

    a2a_capability_service.register_capability(capability1_metadata)
    a2a_capability_service.register_capability(capability2_metadata)

    capabilities_list = a2a_capability_service.list_capabilities()

    assert len(capabilities_list) == 2
    capability_names = [cap.name for cap in capabilities_list]
    assert "SummarizeText" in capability_names
    assert "AnotherCapability" in capability_names
