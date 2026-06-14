from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class EvaluationEntity(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id", ondelete="CASCADE"), nullable=False)
    prompt_key: Mapped[str] = mapped_column(Text, nullable=False)
    eval_model: Mapped[str] = mapped_column(Text, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1: Mapped[float] = mapped_column(Float, nullable=False)
    supported_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unsupported_count: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    connectivity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_graph_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hallucination_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    omission_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    ged: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_relation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    judge_prompt_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    judge_prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    triple_verdicts: Mapped[list["EvaluationTripleVerdictEntity"]] = relationship(
        "EvaluationTripleVerdictEntity",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )
    missing_relations: Mapped[list["EvaluationMissingRelationEntity"]] = relationship(
        "EvaluationMissingRelationEntity",
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class EvaluationTripleVerdictEntity(Base):
    __tablename__ = "evaluation_triple_verdicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    triple: Mapped[str] = mapped_column(Text, nullable=False)
    supported: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    evaluation: Mapped["EvaluationEntity"] = relationship(
        "EvaluationEntity",
        back_populates="triple_verdicts",
    )


class EvaluationMissingRelationEntity(Base):
    __tablename__ = "evaluation_missing_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    relation: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation: Mapped["EvaluationEntity"] = relationship(
        "EvaluationEntity",
        back_populates="missing_relations",
    )
