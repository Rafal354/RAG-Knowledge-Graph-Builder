import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api import router as health_router, startup_event, shutdown_event
from app.articles.api import router as articles_router
from app.evaluation.api import router as evaluation_router
from app.graph.api import router as graphs_router
from app.kb.prompt_config_api import router as prompt_config_router
from app.model.api import router as model_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_event()
    yield
    shutdown_event()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(articles_router)
app.include_router(graphs_router)
app.include_router(model_router)
app.include_router(evaluation_router)
app.include_router(prompt_config_router)

IN_DOCKER = os.path.exists("/.dockerenv")
if not IN_DOCKER:
    frontend_dir = Path(__file__).parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
