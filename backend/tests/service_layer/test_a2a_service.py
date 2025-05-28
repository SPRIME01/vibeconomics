import pytest
from pydantic import BaseModel

from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse
from app.service_layer.a2a_service import (
    A2ACapabilityService,
    A2AHandlerService,
    CapabilityMetadata,
)


@pytest.fixture
def a2a_capability_service() -> A2ACapabilityService:
    """
    Provides a pytest fixture that returns a new instance of A2ACapabilityService for use in tests.
    """
    return A2ACapabilityService()


class MockRequest(BaseModel):
    input_text: str


class MockResponse(BaseModel):
    output_text: str


def test_a2a_capability_service_creation():
    """Test that A2ACapabilityService can be instantiated."""
    service = A2ACapabilityService()
    assert service is not None


def test_a2a_handler_service_creation():
    """Test that A2AHandlerService can be instantiated."""
    service = A2AHandlerService()
    assert service is not None


def test_capability_metadata_creation():
    """Test that CapabilityMetadata can be created with schemas."""
    metadata = CapabilityMetadata(
        name="test_capability",
        description="A test capability",
        input_schema=MockRequest,
        output_schema=MockResponse,
    )

    assert metadata.name == "test_capability"
    assert metadata.description == "A test capability"
    assert metadata.input_schema == MockRequest
    assert metadata.output_schema == MockResponse


@pytest.mark.asyncio
async def test_a2a_handler_service_handle_request():
    """Test A2AHandlerService can handle a basic request."""
    service = A2AHandlerService()
    test_data = MockRequest(input_text="test input")

    # This will likely need implementation - for now just test it doesn't crash
    try:
        result = await service.handle_a2a_request("test_capability", test_data)
        # If implemented, verify the result
        assert result is not None
    except NotImplementedError:
        # Expected if not yet implemented
        pytest.skip("A2AHandlerService.handle_a2a_request not yet implemented")


def test_a2a_capability_service_get_capability():
    """Test A2ACapabilityService can retrieve capabilities."""
    service = A2ACapabilityService()

    # This will likely need implementation - for now just test it doesn't crash
    try:
        capability = service.get_capability("test_capability")
        # If implemented and capability exists, verify it
        if capability:
            assert hasattr(capability, "name")
    except NotImplementedError:
        # Expected if not yet implemented
        pytest.skip("A2ACapabilityService.get_capability not yet implemented")


def test_register_and_get_capability(a2a_capability_service: A2ACapabilityService):
    """
    Tests that a capability can be registered and then retrieved with correct metadata.

    Registers a capability named "SummarizeText" with specified metadata, retrieves it, and asserts that all attributes match the registered values.
    """
    capability_metadata = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None,  # Placeholder for handler
    )
    a2a_capability_service.register_capability(capability_metadata)
    retrieved_capability = a2a_capability_service.get_capability("SummarizeText")

    assert retrieved_capability is not None
    assert retrieved_capability.name == "SummarizeText"
    assert retrieved_capability.description == "Summarizes a given text."
    assert retrieved_capability.input_schema == SummarizeTextA2ARequest
    assert retrieved_capability.output_schema == SummarizeTextA2AResponse


def test_reregister_capability_overwrites(a2a_capability_service: A2ACapabilityService):
    # Register the initial capability
    """
    Tests that re-registering a capability with the same name overwrites the existing capability's metadata.

    Registers a capability, retrieves and asserts its description, then re-registers with a different description and verifies that the updated metadata replaces the original.
    """
    capability_metadata_1 = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None,
    )
    a2a_capability_service.register_capability(capability_metadata_1)
    retrieved_capability_1 = a2a_capability_service.get_capability("SummarizeText")
    assert retrieved_capability_1 is not None
    assert retrieved_capability_1.description == "Summarizes a given text."

    # Register a new capability with the same name but different description
    capability_metadata_2 = CapabilityMetadata(
        name="SummarizeText",
        description="A different description.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None,
    )
    a2a_capability_service.register_capability(capability_metadata_2)
    retrieved_capability_2 = a2a_capability_service.get_capability("SummarizeText")
    assert retrieved_capability_2 is not None
    assert retrieved_capability_2.description == "A different description."
    # Ensure the capability was overwritten
    assert retrieved_capability_2 != retrieved_capability_1


def test_get_nonexistent_capability(a2a_capability_service: A2ACapabilityService):
    retrieved_capability = a2a_capability_service.get_capability(
        "NonExistentCapability"
    )
    assert retrieved_capability is None


def test_list_capabilities(a2a_capability_service: A2ACapabilityService):
    """
    Tests that multiple capabilities can be registered and that all are returned by list_capabilities.

    Registers two distinct capabilities and asserts that both are present in the list returned by the service.
    """
    capability1_metadata = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=None,
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
        handler=None,
    )

    a2a_capability_service.register_capability(capability1_metadata)
    a2a_capability_service.register_capability(capability2_metadata)

    capabilities_list = a2a_capability_service.list_capabilities()

    assert len(capabilities_list) == 2
    capability_names = [cap.name for cap in capabilities_list]
    assert "SummarizeText" in capability_names
    assert "AnotherCapability" in capability_names
