import os
import sys
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core import run_agent_chat, SESSION_STORE, SYSTEM_METRICS

app = FastAPI(
    title="Trendly FDE Agentic Support API",
    description="Forward Deployed Engineer Intern Screening Assignment - Yellow.ai",
    version="1.0.0"
)

# Enable CORS for browser and multi-origin evaluations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/metrics")
def get_metrics():
    """Observability endpoint returning real-time agent metrics."""
    return {
        "status": "healthy",
        "system": "Trendly Support Agent",
        "metrics": SYSTEM_METRICS
    }

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

@app.get("/ui", response_class=HTMLResponse)
async def get_chat_ui():
    session_id = f"web-{uuid.uuid4().hex[:6]}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trendly AI Assistant</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; display: flex; justify-content: center; padding: 20px; }}
            #chat-container {{ width: 100%; max-width: 500px; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: 80vh; }}
            #header {{ background: #111827; color: white; padding: 16px; border-radius: 12px 12px 0 0; text-align: center; font-weight: bold; }}
            #messages {{ flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; }}
            .message {{ max-width: 80%; padding: 10px 14px; border-radius: 18px; line-height: 1.4; font-size: 15px; }}
            .bot {{ background: #f3f4f6; color: #1f2937; align-self: flex-start; border-bottom-left-radius: 4px; }}
            .user {{ background: #2563eb; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
            #input-area {{ display: flex; padding: 16px; border-top: 1px solid #e5e7eb; }}
            input {{ flex: 1; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; outline: none; font-size: 15px; }}
            button {{ margin-left: 10px; padding: 10px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }}
            button:hover {{ background: #1d4ed8; }}
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="header">Trendly Support</div>
            <div id="messages">
                <div class="message bot">Hi there! I'm the Trendly Support Assistant. How can I help you with your order?</div>
            </div>
            <div id="input-area">
                <input type="text" id="userInput" placeholder="Type your message..." onkeypress="if(event.key === 'Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            const sessionId = "{session_id}";
            const messagesDiv = document.getElementById('messages');
            const inputField = document.getElementById('userInput');

            function appendMessage(text, sender) {{
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${{sender}}`;
                msgDiv.innerText = text;
                messagesDiv.appendChild(msgDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }}

            async function sendMessage() {{
                const text = inputField.value.trim();
                if (!text) return;
                
                appendMessage(text, 'user');
                inputField.value = '';
                appendMessage('...', 'bot');
                const typingIndicator = messagesDiv.lastChild;

                try {{
                    const response = await fetch('/chat', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ session_id: sessionId, message: text }})
                    }});
                    const data = await response.json();
                    messagesDiv.removeChild(typingIndicator);
                    appendMessage(data.response, 'bot');
                }} catch (error) {{
                    messagesDiv.removeChild(typingIndicator);
                    appendMessage('Sorry, I encountered an error connecting to the server.', 'bot');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.main:app", host="0.0.0.0", port=8000, reload=True)