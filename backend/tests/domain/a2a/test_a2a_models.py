import pytest
from pydantic import BaseModel
from typing import Type


from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse

def test_summarize_text_a2a_request_serialization_deserialization():
    original_request = SummarizeTextA2ARequest(text_to_summarize="This is a long text that needs summarization.")
    json_data = original_request.model_dump_json()
    deserialized_request = SummarizeTextA2ARequest.model_validate_json(json_data)
    assert deserialized_request == original_request


def test_summarize_text_a2a_response_serialization_deserialization():
    original_response = SummarizeTextA2AResponse(summary="This is the summary.")
    json_data = original_response.model_dump_json()
    deserialized_response = SummarizeTextA2AResponse.model_validate_json(json_data)
    assert deserialized_response == original_response


class SummarizeTextCapabilityMetadata(BaseModel):
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    class Config:
        arbitrary_types_allowed = True


def test_summarize_text_capability_metadata():
    metadata = SummarizeTextCapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
    )
    assert metadata.name == "SummarizeText"
    assert metadata.input_schema == SummarizeTextA2ARequest
    assert metadata.output_schema == SummarizeTextA2AResponse
