import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.clients.llm.groq import llm_client
from app.core.db import get_db
from app.rag.service import retrieve_context
from app.security.waf import check_prompt_injection
from app.security.ratelimit import check_rate_limit

router = APIRouter(prefix="/chat", tags=["chat"])

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[MessageItem] = [] # <-- NEW: Accepts previous messages

class ChatResponse(BaseModel):
    reply: str

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not llm_client.api_key:
        raise HTTPException(status_code=500, detail="Groq API key is missing in .env")

    # 0. Rate Limit
    await check_rate_limit(str(current_user.id))

    # 1. Security: Check for Prompt Injection
    if check_prompt_injection(payload.message):
        return ChatResponse(reply="⚠️ Security Alert: Your message was flagged for prompt injection. Please ask a valid question.")

    # 2. RAG: Search the database
    rag_context = await retrieve_context(payload.message, db)

    # 3. Build the prompt
    system_prompt = (
        "You are FelChat, a highly intelligent, professional, and security-focused AI assistant. "
        "You have access to a database of real CVEs AND information about Felix Otieno's cybersecurity portfolio projects (zero-trust-gateway, cloud-native-siem, recon-platform, honeypot-factory, felchat). If the user asks about Felix or his projects, use the context to describe them.\n\n"
        f"--- CONTEXT ---\n{rag_context}\n---------------\n"
    )

    # 4. Assemble the full conversation (System + History + Current Message)
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add the history sent from the frontend
    for msg in payload.history:
        messages.append({"role": msg.role, "content": msg.content})
        
    # Add the current user message
    messages.append({"role": "user", "content": payload.message})

    try:
        reply = await llm_client.chat(messages)
        return ChatResponse(reply=reply)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Groq Error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
