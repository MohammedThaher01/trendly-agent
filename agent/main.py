import os
import sys

if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.core import run_agent_chat, SESSION_STORE

app = FastAPI(
    title="Trendly FDE Agentic Support API",
    description="Forward Deployed Engineer Intern Screening Assignment - Yellow.ai",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

@app.get("/")
def health_check():
    return {"status": "online", "system": "Trendly Support Agent", "eval_date": "2026-08-04"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    bot_reply = run_agent_chat(payload.session_id, payload.message)
    return ChatResponse(session_id=payload.session_id, response=bot_reply)

@app.post("/reset")
def reset_session(session_id: str):
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
        return {"status": "cleared", "session_id": session_id}
    return {"status": "not_found", "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="0.0.0.0", port=8000, reload=True)
