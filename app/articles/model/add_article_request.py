from pydantic import Field, BaseModel


class AddArticleRequest(BaseModel):
    title: str = Field(..., description="Article title")
    text: str = Field(..., description="Article content")
