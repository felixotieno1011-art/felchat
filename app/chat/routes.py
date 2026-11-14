import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.clients.llm.groq import llm_client
from app.core.db import get_db
from app.rag.service import retrieve_context
from app.security.waf import check_prompt_injection
from app.security.ratelimit import check_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[MessageItem] = []

@router.post("/message")
async def send_message(
    payload: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not llm_client.api_key:
        raise HTTPException(status_code=500, detail="Groq API key is missing.")

    await check_rate_limit(str(current_user.id))

    # WAF Check
    if check_prompt_injection(payload.message):
        # If blocked, stream a single chunk
        async def blocked():
            yield "⚠️ Security Alert: Your message was flagged for prompt injection."
        return StreamingResponse(blocked(), media_type="text/plain")

    # RAG Context
    rag_context = await retrieve_context(payload.message, db)

    system_prompt = (
        "You are FelChat, a highly intelligent, professional, and security-focused AI assistant. "
        "You have a live web search tool. If the user asks about recent events, sports, news, or anything that happened after mid-2024, you MUST use the web search tool. "
        "If the provided context contains CVE data, use it. If the user asks for a CVE and the context says 'No details found', explicitly tell them.\n\n"
        f"{rag_context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in payload.history:
        if msg.role in ["user", "assistant"]:
            if "⚠️ Security Alert" in msg.content or "Network error" in msg.content:
                continue
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": payload.message})

    async def stream_generator():
        try:
            async for chunk in llm_client.stream_chat(messages):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming Error: {e}")
            yield "\n\n[Error: The AI connection was interrupted.]"

    return StreamingResponse(stream_generator(), media_type="text/plain")
