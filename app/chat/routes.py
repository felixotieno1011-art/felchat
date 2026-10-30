from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.clients.llm.groq import llm_client

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest, 
    current_user: User = Depends(get_current_user)
):
    if not llm_client.api_key:
        raise HTTPException(status_code=500, detail="Groq API key is missing in .env")

    # FelChat System Persona
    system_prompt = (
        "You are FelChat, a highly intelligent, professional, and security-focused AI assistant. "
        "You answer general questions accurately but excel at cybersecurity, programming, and logic. "
        "Keep your answers concise and helpful."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.message}
    ]

    try:
        reply = await llm_client.chat(messages)
        return ChatResponse(reply=reply)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Groq Error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
