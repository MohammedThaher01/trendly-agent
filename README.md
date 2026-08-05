# Trendly Support Agent - Yellow.ai FDE Assignment

An agentic support assistant built for Trendly, capable of handling multi-turn support chats, processing complex return/exchange logic deterministically, and knowing exactly when to escalate to a human.

## Quick Start

1. **Clone and setup environment**
git clone <your-repo-url>
cd trendly-support-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

2. **Install dependencies**
pip install -r requirements.txt

3. **Configure Environment**
Create a `.env` file in the project root:
GROQ_API_KEY=your_groq_api_key_here

4. **Run the Live Server**
python main.py

The API will be available at `http://localhost:8000`. You can interact with the agent via the `/chat` endpoint using any HTTP client.

## Endpoints

- `GET /`: Health check and system status.
- `POST /chat`: Submit a message. Requires `{"session_id": "string", "message": "string"}`.
- `POST /reset`: Clear conversation history for a given `session_id`.

## AI Usage Note
I used an LLM to rapidly template the FastAPI boilerplate and brainstorm strict system prompt guardrails. The hybrid architecture (separating the LLM orchestrator from the deterministic Python business logic) and the exact tool implementations were heavily guided and modified by me to ensure zero hallucination on the rigid policy rules.