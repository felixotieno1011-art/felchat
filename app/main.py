from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.logs.routes import router as logs_router
from app.core.redis import close_redis
import logging

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload RAG model at startup (prevents freeze on first request)
    logger.info("Preloading RAG embedding model...")
    try:
        from app.rag.service import get_model
        get_model()
        logger.info("RAG model loaded successfully.")
    except Exception as e:
        logger.error(f"RAG model failed to load: {e}")

    yield
    await close_redis()

app = FastAPI(title="FelChat API", version="1.0.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(logs_router)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))
