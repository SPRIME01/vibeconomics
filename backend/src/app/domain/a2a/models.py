from pydantic import BaseModel


class SummarizeTextA2ARequest(BaseModel):
    """Request model for text summarization A2A capability."""

    text: str
    max_length: int | None = None


class SummarizeTextA2AResponse(BaseModel):
    """Response model for text summarization A2A capability."""

    summary: str
    original_length: int
    summary_length: int
