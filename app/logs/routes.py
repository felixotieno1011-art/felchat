from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.logs.service import analyze_log_file
from app.clients.llm.groq import llm_client

router = APIRouter(prefix="/logs", tags=["logs"])

@router.post("/analyze")
async def analyze_log(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.log', '.txt')):
        raise HTTPException(status_code=400, detail="Only .log or .txt files allowed")

    content = await file.read()
    try:
        text = content.decode('utf-8', errors='ignore')
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read file")

    # 1. Run local Python analysis
    report = analyze_log_file(text)

    if report["total_lines"] == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # 2. Ask the AI to explain the findings
    system_prompt = "You are FelChat, a cybersecurity analyst. Explain the following log analysis findings to the user in a clear, concise way. Highlight the severity of the threats."
    user_prompt = f"Log Analysis Report:\n- Total Lines: {report['total_lines']}\n- Failed Logins: {report['failed_logins']}\n- Path Traversals: {report['path_traversals']}\n- Top Attacking IPs: {report['top_attacking_ips']}\n\nPlease summarize this and recommend mitigations."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_analysis = await llm_client.chat(messages)
        return {
            "report": report,
            "ai_analysis": ai_analysis
        }
    except Exception as e:
        return {
            "report": report,
            "ai_analysis": f"Could not generate AI summary: {str(e)}"
        }
