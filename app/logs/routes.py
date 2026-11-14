from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.logs.service import analyze_log_file
from app.clients.llm.groq import llm_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/logs", tags=["logs"])

@router.post("/analyze")
async def analyze_log(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.lower().endswith(('.log', '.txt')):
        raise HTTPException(status_code=400, detail="Only .log or .txt files allowed")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")

    try:
        text = content.decode('utf-8', errors='ignore')
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read file")

    report = analyze_log_file(text)
    if report["total_lines"] == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    system_prompt = "You are FelChat, a cybersecurity analyst. Explain these log findings and highlight any brute-force successes."
    user_prompt = f"Findings:\n{report}"

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    try:
        ai_analysis = await llm_client.chat(messages)
        return {"report": report, "ai_analysis": ai_analysis}
    except Exception as e:
        logger.error(f"Groq Log Analysis Error: {str(e)}")
        return {"report": report, "ai_analysis": "Could not generate AI summary at this time."}
