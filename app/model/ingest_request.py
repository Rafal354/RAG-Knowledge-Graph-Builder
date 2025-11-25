from openai import BaseModel
from pydantic import Field


class IngestRequest(BaseModel):
    title: str = Field(..., description="Article title")
    text: str = Field(..., description="Article content")