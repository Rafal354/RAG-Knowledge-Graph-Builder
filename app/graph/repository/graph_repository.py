import logging

from sqlalchemy.orm import selectinload

from app.config.database import SessionLocal
from app.graph.model.graph_entity import GraphEntity, GraphRelationEntity
from app.graph.model.graph import GraphDetails

logger = logging.getLogger(__name__)


class GraphRepository:
    def save_graph(self, relations: list[tuple[str, str, str]]) -> GraphDetails:
        with SessionLocal() as session:
            try:
                latest_version_row = (
                    session.query(GraphEntity.version)
                    .order_by(GraphEntity.version.desc())
                    .first()
                )
                next_version = (latest_version_row[0] if latest_version_row else 0) + 1

                logger.info(f"Next graph version: {next_version}")

                graph = GraphEntity(version=next_version)
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

    @staticmethod
    def _map_to_details(graph: GraphEntity | None) -> GraphDetails | None:
        if graph is None:
            return None

        return GraphDetails.from_entity(graph)
