# Trendly Agentic Support API 
**Yellow.ai Forward Deployed Engineer Intern Assignment**

An enterprise-grade support agent built for Trendly. Designed to handle 2,000+ daily chats, this system processes complex return/exchange logic deterministically, grounds policy answers strictly in documentation, and escalates edge cases cleanly to a human CRM.

## 🚀 Live Demo & Endpoints

The application is deployed live on Render and will remain active for the evaluation period.

*   **Live Chat UI:** [https://yellow-ai-trendy-agent.onrender.com/ui](https://yellow-ai-trendy-agent.onrender.com/ui) *(Vanilla HTML/JS interface)*
*   **API Documentation (Swagger):** [https://yellow-ai-trendy-agent.onrender.com/docs](https://yellow-ai-trendy-agent.onrender.com/docs)
*   **Real-time Observability:** [https://yellow-ai-trendy-agent.onrender.com/metrics](https://yellow-ai-trendy-agent.onrender.com/metrics)

## 🧠 Architectural Highlights (The FDE Approach)

Rather than wrapping a thin prompt around an LLM, this solution utilizes a hybrid **ReAct (Reasoning and Acting)** architecture:
1.  **The Brain (LLM Orchestrator):** Handles NLU, multi-turn state, and empathy.
2.  **The Brawn (Deterministic Python Tools):** LLMs are historically terrible at date-math and complex boolean logic. All return windows, final-sale checks, and hygiene-category rules are executed via rigid Python logic, eliminating hallucinations.
3.  **The Shield (Security Guardrails):** 
    *   *Input Scrubber:* Intercepts user messages and regex-masks PII (Credit Cards/Phone numbers) before they ever reach the LLM.
    *   *Output Validator:* Blocks unauthorized policy generation and enforces Section 7 rules (no bank detail collection).

## 💻 Quick Start (Local Setup)

1. **Clone the repository**
   ```bash
   git clone https://github.com/MohammedThaher01/yellow-ai-trendy-agent
   cd yellow-ai-trendy-agent
   ```

2. **Set up the virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Run the server**
   ```bash
   uvicorn agent.main:app --reload --port 8000
   ```

   The server starts at `http://localhost:8000`.
   - UI: `http://localhost:8000/ui`
   - Swagger docs: `http://localhost:8000/docs`
