from pydantic import BaseModel, Field

from app.graph.graph_entity import GraphEntity


class GraphRelationDetails(BaseModel):
    entity_1: str = Field(..., description="Source entity")
    relation: str = Field(..., description="Relation type")
    entity_2: str = Field(..., description="Target entity")



class GraphDetails(BaseModel):
    graph_id: int = Field(..., description="Graph identifier")
    version: int = Field(..., description="Graph version")
    created_at: str = Field(..., description="Graph creation timestamp")
    relations: list[GraphRelationDetails] = Field(default_factory=list)

    @classmethod
    def from_entity(cls, graph: GraphEntity) -> "GraphDetails":
        return cls(
            graph_id=graph.id,
            version=graph.version,
            created_at=graph.created_at.isoformat(),
            relations=[
                GraphRelationDetails(
                    entity_1=relation.entity_1,
                    relation=relation.relation,
                    entity_2=relation.entity_2,
                )
                for relation in graph.relations
            ],
        )