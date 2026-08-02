from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class GraphEntity(Base):
    __tablename__ = "graphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    article_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    prompt_key: Mapped[str | None] = mapped_column(Text, ForeignKey("prompts.key", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    relations: Mapped[list["GraphRelationEntity"]] = relationship(
        "GraphRelationEntity",
        back_populates="graph",
        cascade="all, delete-orphan",
    )


class GraphMergeStatsEntity(Base):
    """Statystyki scalania dla pojedynczego kroku scenariusza przyrostowego (4.7) -
    ile trójek istniało, ile zaproponowano świeżo z izolowanej ekstrakcji, ile z nich
    odrzucono jako dokładne duplikaty (po normalizacji) przy save_incremental_graph."""

    __tablename__ = "graph_merge_stats"

    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id", ondelete="CASCADE"), primary_key=True)
    existing_count: Mapped[int] = mapped_column(Integer, nullable=False)
    new_candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    merged_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dropped_count: Mapped[int] = mapped_column(Integer, nullable=False)


class GraphRelationEntity(Base):
    __tablename__ = "graph_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id"), nullable=False)

    entity_1: Mapped[str] = mapped_column(Text, nullable=False)
    relation: Mapped[str] = mapped_column(Text, nullable=False)
    entity_2: Mapped[str] = mapped_column(Text, nullable=False)

    graph: Mapped["GraphEntity"] = relationship(
        "GraphEntity",
        back_populates="relations",
    )
