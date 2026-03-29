# api/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api.config import settings
from api.db import ensure_schema
from api.queue import start_worker

# Module routers
from api.modules.skills.router import router as skills_router
from api.modules.ingestion.router import router as ingestion_router
from api.modules.classification.router import router as classification_router
from api.modules.articles.router import router as articles_router
from api.modules.cms.router import router as cms_router
from api.modules.public.router import router as public_router

# Legacy prototype endpoints: wizard, chat, KB viewer, admin panel
from api.legacy_router import router as legacy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    start_worker()
    yield


app = FastAPI(title="MCCAA Knowledge Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all module routers
app.include_router(skills_router)
app.include_router(ingestion_router)
app.include_router(classification_router)
app.include_router(articles_router)
app.include_router(cms_router)
app.include_router(public_router)
app.include_router(legacy_router)


@app.get("/health")
def health():
    return {"status": "ok"}
