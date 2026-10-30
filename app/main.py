from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router

app = FastAPI(title="FelChat API", version="0.2.0")

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
