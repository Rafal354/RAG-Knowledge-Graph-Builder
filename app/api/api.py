import logging
import os
import threading
import webbrowser

from fastapi import APIRouter

from app.articles.model.article_entity import Base
import app.evaluation.model.evaluation_entity  # noqa: F401
import app.kb.model.prompt_entity  # noqa: F401
import app.kb.model.prompt_config_entity  # noqa: F401
from app.config.database import engine
from app.config.settings import settings
from app.kb.knowledge_base_service import knowledge_base_service
from app.neo4j.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)
router = APIRouter()
neo4j_service: Neo4jService | None = None

ARTICLE_NOT_FOUND = "Article not found"


def _seed_prompts() -> None:
    from app.config.database import SessionLocal
    from app.kb.model.prompt_entity import PromptEntity
    from app.kb.prompts import PROMPTS

    with SessionLocal() as session:
        for prompt_set, types in PROMPTS.items():
            for prompt_type, content in types.items():
                key = f"{prompt_set}/{prompt_type}"
                existing = session.get(PromptEntity, key)
                if existing is None:
                    session.add(PromptEntity(key=key, content=content))
                else:
                    existing.content = content
        session.commit()
    logger.info("Prompts seeded")


def startup_event():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS title TEXT"))
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS model TEXT"))
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL"))
        conn.execute(text("ALTER TABLE graphs ADD COLUMN IF NOT EXISTS prompt_key TEXT REFERENCES prompts(key) ON DELETE SET NULL"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS eval_model TEXT DEFAULT ''"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS connectivity_score FLOAT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS reference_graph_id INTEGER"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS hallucination_rate FLOAT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS omission_rate FLOAT"))
        conn.execute(text("ALTER TABLE prompt_configs ADD COLUMN IF NOT EXISTS examples_positive TEXT"))
        conn.execute(text("ALTER TABLE prompt_configs ADD COLUMN IF NOT EXISTS examples_negative TEXT"))
        conn.execute(text("ALTER TABLE prompt_configs ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'structured'"))
        conn.execute(text("ALTER TABLE prompt_configs ADD COLUMN IF NOT EXISTS custom_content TEXT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS t_precision FLOAT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS t_recall FLOAT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS t_f1 FLOAT"))
        conn.execute(text("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS ged INTEGER"))
        conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'evaluations_graph_id_fkey'
                      AND table_name = 'evaluations'
                ) THEN
                    ALTER TABLE evaluations DROP CONSTRAINT evaluations_graph_id_fkey;
                END IF;
                ALTER TABLE evaluations
                    ADD CONSTRAINT evaluations_graph_id_fkey
                    FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE;

                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'evaluation_triple_verdicts_evaluation_id_fkey'
                      AND table_name = 'evaluation_triple_verdicts'
                ) THEN
                    ALTER TABLE evaluation_triple_verdicts DROP CONSTRAINT evaluation_triple_verdicts_evaluation_id_fkey;
                END IF;
                ALTER TABLE evaluation_triple_verdicts
                    ADD CONSTRAINT evaluation_triple_verdicts_evaluation_id_fkey
                    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE;

                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'evaluation_missing_relations_evaluation_id_fkey'
                      AND table_name = 'evaluation_missing_relations'
                ) THEN
                    ALTER TABLE evaluation_missing_relations DROP CONSTRAINT evaluation_missing_relations_evaluation_id_fkey;
                END IF;
                ALTER TABLE evaluation_missing_relations
                    ADD CONSTRAINT evaluation_missing_relations_evaluation_id_fkey
                    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE;
            END $$;
        """))
        conn.commit()
    _seed_prompts()
    from app.kb.prompt_config_service import prompt_config_service
    prompt_config_service.seed_builtins()
    global neo4j_service
    neo4j_service = Neo4jService(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    knowledge_base_service.neo4j_service = neo4j_service
    logger.info("Neo4j driver initialized")
    if not os.path.exists("/.dockerenv"):
        frontend_url = "http://localhost:8000"
        logger.info("Frontend available at: %s", frontend_url)
        threading.Timer(1.5, webbrowser.open, args=[frontend_url]).start()


def shutdown_event():
    knowledge_base_service.shutdown()
    global neo4j_service
    if neo4j_service is not None:
        neo4j_service.close()
        logger.info("Neo4j driver closed")
        neo4j_service = None


@router.get("/health", response_model=dict)
async def healthcheck():
    return {
        "status": "ok",
        "neo4j_initialized": neo4j_service is not None,
        "openai_configured": bool(settings.openai_api_key),
    }
