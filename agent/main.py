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
    title="TechGear Support API",
    description="Hybrid ReAct Autonomous Support Agent",
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
    return {"status": "online", "system": "TechGear Support API", "version": "1.0.0"}

@app.get("/metrics")
def get_metrics():
    """Observability endpoint returning real-time agent metrics."""
    return {
        "status": "healthy",
        "system": "TechGear Support API",
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
        <title>TechGear AI Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
            #chat-container {{ width: 100%; max-width: 500px; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: 75vh; margin-bottom: 2rem; }}
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
            <div id="header">TechGear Support</div>
            <div id="messages">
                <div class="message bot">Hi there! I'm the TechGear Support Assistant. How can I help you with your order?</div>
            </div>
            <div id="input-area">
                <input type="text" id="userInput" placeholder="Type your message..." onkeypress="if(event.key === 'Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <footer class="max-w-4xl mx-auto px-6 flex flex-col items-center gap-4">
            <div class="text-sm text-slate-400 font-medium tracking-wide">
              Developed by Mohammed Thaher S
            </div>
            <div class="flex items-center gap-5">
              <a href="https://github.com/MohammedThaher01" target="_blank" rel="noreferrer" class="text-slate-500 hover:text-slate-800 transition-colors" aria-label="GitHub">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd" />
                </svg>
              </a>
              <a href="https://www.linkedin.com/in/mohammed-thaher-s/" target="_blank" rel="noreferrer" class="text-slate-500 hover:text-[#0a66c2] transition-colors" aria-label="LinkedIn">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fill-rule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clip-rule="evenodd" />
                </svg>
              </a>
              <a href="mailto:thahercareer@gmail.com" class="text-slate-500 hover:text-rose-500 transition-colors" aria-label="Email">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                </svg>
              </a>
            </div>
            <!-- Dataset Link -->
            <div class="mt-2 text-sm">
                <a href="https://github.com/MohammedThaher01/trendly-agent/tree/main/data" target="_blank" rel="noreferrer" class="text-blue-500 hover:text-blue-600 hover:underline transition-colors font-medium">
                    dataset
                </a>
            </div>
        </footer>

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
