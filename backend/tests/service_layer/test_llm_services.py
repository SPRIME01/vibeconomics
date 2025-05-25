import pytest
from typing import Type, Any
from pydantic import BaseModel, Field
from unittest.mock import MagicMock

from app.service_layer.llm_services import AbstractLLMService, DSPyLLMService, PydanticModelT
import dspy # Import dspy for Prediction and settings

# Define the Pydantic model as specified in the issue
class SampleStructuredOutput(BaseModel):
    answer: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)

# Mock DSPy LM client for testing
@pytest.fixture
def mock_dspy_lm_client() -> MagicMock: # self removed
    client = MagicMock()
    # Mock a basic request method for the get_response placeholder
    def mock_basic_request(prompt: str, **kwargs: Any) -> str:
        return f"Mocked LLM response to: {prompt}"
    client.basic_request = mock_basic_request
    
    # For dspy.predict usage in DSPyLLMService's get_response:
    # This mock will be configured further in the test itself.
    return client

@pytest.fixture
def dspy_llm_service(mock_dspy_lm_client: MagicMock) -> DSPyLLMService[BaseModel]: # self removed
    return DSPyLLMService[BaseModel](llm_client=mock_dspy_lm_client)

def test_dspy_llm_service_get_response(
    dspy_llm_service: DSPyLLMService[BaseModel],
    mock_dspy_lm_client: MagicMock
) -> None:
    """Test the basic get_response method of DSPyLLMService."""
    prompt = "Hello, LLM!"
    
    # Configure DSPy settings to use the mock client for this test context
    # This is important if dspy.predict() is used without an explicit lm argument
    # and relies on the global setting.
    original_lm = dspy.settings.lm # Store original to restore later
    dspy.settings.configure(lm=mock_dspy_lm_client)
    
    # The DSPyLLMService's get_response uses a dspy.Predict(BasicQA)
    # which eventually calls the configured LM.
    # The LM (mock_dspy_lm_client in this case) should return a list of dspy.Prediction objects
    # or a list of strings if the signature is simple.
    # For BasicQA (question -> answer), a list of dicts like [{'answer': '...'}, ...] or
    # a dspy.Prediction object with an 'answer' attribute is expected by some DSPy internals.
    # Let's make the mock client return a list containing a dspy.Prediction object.
    
    # Create a mock dspy.Prediction object
    # Note: dspy.Prediction is a simple class, but dspy.Completions (plural) is often returned by LMs
    # For dspy.Predict(Signature), the LM's __call__ method is expected to return a list of
    # dspy.Prediction instances or dicts that can be parsed into the signature fields.
    # For a signature "input -> output", the LM needs to return something that dspy.Predict
    # can interpret to populate `response.output`.
    # If the signature is `question -> answer` (like BasicQA), it would be `response.answer`.

    # The `get_response` method in `DSPyLLMService` uses this logic:
    # `with dspy.context(lm=self.llm_client):`
    # `  response = dspy.predict(dspy.Signature("input -> output", ...))(input=prompt)`
    # `  return response.output`
    # So, `mock_dspy_lm_client` needs to be callable and return an object with an `output` attribute.
    # A simple way is to make the mock client's `__call__` or `return_value` (if it's a general mock)
    # provide this structure. Since `dspy.predict` wraps the call, the `mock_dspy_lm_client` itself
    # is the LM that `dspy.predict` will use.
    
    # When `dspy.predict(Signature)(input=prompt)` is called, and `self.llm_client` is the LM,
    # `self.llm_client.__call__` will be invoked.
    # It should return a list of `dspy.Example` or `dspy.Prediction` like objects or dicts.
    # For a signature like "input -> output", it needs to provide an "output" field.
    
    # Let's mock the return value of the llm_client when it's called by DSPy's machinery.
    # This simulates the LM generating a response.
    # dspy.predict expects the LM to return a list of completions.
    # Each completion should be a dictionary or an object that can be treated like one,
    # matching the output fields of the signature.
    # For "input -> output", it expects a list of dicts like `[{'output': 'response_text'}]`
    mock_dspy_lm_client.return_value = [{"output": f"Mocked LLM response to: {prompt}"}]

    response_text = dspy_llm_service.get_response(prompt)
    assert response_text == f"Mocked LLM response to: {prompt}"
    
    # Restore original DSPy settings
    dspy.settings.configure(lm=original_lm)


def test_dspy_llm_service_generates_structured_output(
    dspy_llm_service: DSPyLLMService[SampleStructuredOutput], # Specify ModelT
) -> None:
    """Test DSPy service generates output conforming to a Pydantic model via Outlines (mocked)."""
    question: str = "What is 2 + 2?"
    
    response = dspy_llm_service.get_structured_response(
        prompt=question,
        output_model=SampleStructuredOutput
    )
    assert isinstance(response, SampleStructuredOutput)
    assert response.answer == "4"
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    assert response.confidence == 0.99

def test_dspy_llm_service_structured_output_handles_generic_mock() -> None:
    """Test the generic mock data generation for structured output."""
    class AnotherModel(BaseModel):
        name: str
        value: int
        is_valid: bool
        ratio: float

    service = DSPyLLMService[AnotherModel](llm_client=MagicMock())
    response = service.get_structured_response(
        prompt="Generate something for AnotherModel",
        output_model=AnotherModel
    )
    assert isinstance(response, AnotherModel)
    assert response.name == "mock string"
    assert response.value == 0
    assert response.is_valid is False
    assert response.ratio == 0.0
