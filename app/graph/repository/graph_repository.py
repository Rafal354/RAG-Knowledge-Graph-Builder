import logging

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.config.database import SessionLocal
from app.graph.model.graph import GraphDetails, GraphSummary
from app.graph.model.graph_entity import GraphEntity, GraphRelationEntity

logger = logging.getLogger(__name__)


class GraphRepository:
    def save_graph(self, relations: list[tuple[str, str, str]], title: str | None = None, model: str | None = None, article_id: int | None = None, prompt_key: str | None = None) -> GraphDetails:
        with SessionLocal() as session:
            try:
                latest_version_row = (
                    session.query(GraphEntity.version)
                    .order_by(GraphEntity.version.desc())
                    .first()
                )
                next_version = (latest_version_row[0] if latest_version_row else 0) + 1

                max_position_row = session.query(func.max(GraphEntity.position)).scalar()
                next_position = (max_position_row if max_position_row is not None else 0) + 1

                logger.info(f"Next graph version: {next_version}, position: {next_position}")

                graph = GraphEntity(version=next_version, position=next_position, title=title, model=model, article_id=article_id, prompt_key=prompt_key)
                session.add(graph)
                session.flush()

                logger.info(f"Created graph row with id={graph.id}")

                for entity_1, relation, entity_2 in relations:
                    session.add(
                        GraphRelationEntity(
                            graph_id=graph.id,
                            entity_1=entity_1,
                            relation=relation,
                            entity_2=entity_2,
                        )
                    )

                session.commit()
                logger.info("Graph committed successfully")

                saved_graph = (
                    session.query(GraphEntity)
                    .options(selectinload(GraphEntity.relations))
                    .filter(GraphEntity.id == graph.id)
                    .first()
                )

                logger.info(f"Saved graph after commit: {saved_graph}")

                return self._map_to_details(saved_graph)

            except Exception:
                session.rollback()
                logger.exception("Failed to save graph")
                raise

    def get_latest_graph(self) -> GraphEntity | None:
        with SessionLocal() as session:
            return (
                session.query(GraphEntity)
                .options(selectinload(GraphEntity.relations))
                .order_by(GraphEntity.version.desc())
                .first()
            )

    def get_all_graphs(self) -> list[GraphSummary]:
        with SessionLocal() as session:
            graphs = (
                session.query(GraphEntity)
                .options(selectinload(GraphEntity.relations))
                .order_by(GraphEntity.version.desc())
                .all()
            )
            return [
                GraphSummary(
                    graph_id=g.id,
                    version=g.version,
                    position=g.position,
                    created_at=g.created_at.isoformat(),
                    relation_count=len(g.relations),
                    title=g.title,
                    model=g.model,
                    article_id=g.article_id,
                    prompt_key=g.prompt_key,
                )
                for g in graphs
            ]

    def get_graph(self, graph_id: int) -> GraphEntity | None:
        with SessionLocal() as session:
            return (
                session.query(GraphEntity)
                .options(selectinload(GraphEntity.relations))
                .filter(GraphEntity.id == graph_id)
                .first()
            )

    def update_graph_position(self, graph_id: int, position: int) -> bool:
        with SessionLocal() as session:
            graph = session.query(GraphEntity).filter(GraphEntity.id == graph_id).first()
            if graph is None:
                return False
            graph.position = position
            session.commit()
            return True

    def delete_graph(self, graph_id: int) -> bool:
        with SessionLocal() as session:
            graph = session.query(GraphEntity).filter(GraphEntity.id == graph_id).first()
            if graph is None:
                return False
            session.delete(graph)
            session.commit()
            return True

    @staticmethod
    def _map_to_details(graph: GraphEntity | None) -> GraphDetails | None:
        if graph is None:
            return None

        return GraphDetails.from_entity(graph)
