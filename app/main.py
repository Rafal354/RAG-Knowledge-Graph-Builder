import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.controller import router, startup_event, shutdown_event

logger = logging.getLogger(__name__)
# load_dotenv()

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

app.include_router(router)
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)
