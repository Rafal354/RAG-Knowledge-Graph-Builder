import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.controller import router, startup_event, shutdown_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Building Knowledge Base API",
    description="API for receiving article texts and building a graph-based knowledge database.",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routing
app.include_router(router)
# Lifecycle
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

logger.info("Application initialized")