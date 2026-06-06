from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class PromptConfigEntity(Base):
    __tablename__ = "prompt_configs"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    entity_types: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rules: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(Text, nullable=False, default="pl")
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    examples_positive: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples_negative: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="structured")
    custom_content: Mapped[str | None] = mapped_column(Text, nullable=True)
