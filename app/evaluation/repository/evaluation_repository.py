import logging

from sqlalchemy.orm import selectinload

from app.config.database import SessionLocal
from app.evaluation.evaluation_service import EvaluationResult
from app.evaluation.model.evaluation_entity import (
    EvaluationEntity,
    EvaluationMissingRelationEntity,
    EvaluationTripleVerdictEntity,
)

logger = logging.getLogger(__name__)


class EvaluationRepository:

    def save(self, result: EvaluationResult, prompt_key: str) -> EvaluationEntity:
        with SessionLocal() as session:
            try:
                entity = EvaluationEntity(
                    graph_id=result.graph_id,
                    prompt_key=prompt_key,
                    eval_model=result.eval_model,
                    precision=result.precision,
                    recall=result.recall,
                    f1=result.f1,
                    supported_count=result.supported_count,
                    unsupported_count=result.unsupported_count,
                    missing_count=result.missing_count,
                    analysis=result.analysis,
                    connectivity_score=result.connectivity_score,
                    reference_graph_id=result.reference_graph_id,
                    hallucination_rate=result.hallucination_rate,
                    omission_rate=result.omission_rate,
                    t_precision=result.t_precision,
                    t_recall=result.t_recall,
                    t_f1=result.t_f1,
                    ged=result.ged,
                    matched_count=result.matched_count,
                    reference_relation_count=result.reference_relation_count,
                    judge_prompt_version=result.judge_prompt_version,
                    judge_prompt_text=result.judge_prompt_text,
                    unique_entities=result.unique_entities,
                    reference_unique_entities=result.reference_unique_entities,
                    self_duplicate_relations=result.self_duplicate_relations,
                    self_duplicate_rate=result.self_duplicate_rate,
                    merge_new_candidate_count=result.merge_new_candidate_count,
                    merge_dropped_count=result.merge_dropped_count,
                    merge_drop_rate=result.merge_drop_rate,
                )
                session.add(entity)
                session.flush()

                for v in result.triple_verdicts:
                    session.add(EvaluationTripleVerdictEntity(
                        evaluation_id=entity.id,
                        triple=v["triple"],
                        supported=v["supported"],
                        comment=v.get("comment"),
                    ))

                for r in result.missing_relations:
                    session.add(EvaluationMissingRelationEntity(
                        evaluation_id=entity.id,
                        relation=r,
                    ))

                session.commit()
                logger.info("Saved evaluation id=%d for graph_id=%d", entity.id, result.graph_id)
                return entity
            except Exception:
                session.rollback()
                logger.exception("Failed to save evaluation")
                raise

    def get_all(self) -> list[EvaluationEntity]:
        with SessionLocal() as session:
            return (
                session.query(EvaluationEntity)
                .order_by(EvaluationEntity.created_at.desc())
                .all()
            )

    def get(self, evaluation_id: int) -> EvaluationEntity | None:
        with SessionLocal() as session:
            return (
                session.query(EvaluationEntity)
                .options(
                    selectinload(EvaluationEntity.triple_verdicts),
                    selectinload(EvaluationEntity.missing_relations),
                )
                .filter(EvaluationEntity.id == evaluation_id)
                .first()
            )

    def update_judge_prompt_text(self, evaluation_id: int, judge_prompt_text: str) -> None:
        with SessionLocal() as session:
            entity = session.query(EvaluationEntity).filter(EvaluationEntity.id == evaluation_id).first()
            if entity is not None:
                entity.judge_prompt_text = judge_prompt_text
                session.commit()

    def delete(self, evaluation_id: int) -> bool:
        with SessionLocal() as session:
            entity = session.query(EvaluationEntity).filter(EvaluationEntity.id == evaluation_id).first()
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True
