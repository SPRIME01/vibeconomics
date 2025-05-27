from pydantic import BaseModel


class SummarizeTextA2ARequest(BaseModel):
    text_to_summarize: str


class SummarizeTextA2AResponse(BaseModel):
    summary: str
