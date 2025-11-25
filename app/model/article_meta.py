from openai import BaseModel


class ArticleMeta(BaseModel):
    article_id: int
    title: str
    filename: str
    created_at: str
    text_length: int