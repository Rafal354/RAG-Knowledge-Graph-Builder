from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class PromptEntity(Base):
    __tablename__ = "prompts"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
