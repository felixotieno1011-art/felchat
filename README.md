# 🛡️ FelChat — The AI Security Assistant

FelChat is a full-stack, AI-powered security assistant designed to answer cybersecurity questions, analyze CVEs, and scan log files for threats. 

Built from scratch by Felix Otieno as a portfolio project to demonstrate expertise in AI, cybersecurity, and full-stack engineering.

## 🚀 Features
- **Live AI Chat:** Powered by Groq's `gpt-oss-120b` for blazing-fast, general-purpose AI responses.
- **Security RAG (Retrieval-Augmented Generation):** Ingests 500 real CVEs from the NIST database and uses `pgvector` to search them. Answers are grounded in real vulnerability data.
- **AI Log Analyzer:** Upload `.log` files (like SSH auth logs) and FelChat will detect brute-force attempts, path traversals, and generate a professional incident response report.
- **Enterprise Security:** 
  - JWT-based authentication.
  - Prompt Injection Defense (WAF).
  - Rate limiting using Redis.
- **Custom Premium UI:** A responsive, gold-themed interface built with vanilla HTML/CSS/JS.

## 🛠️ Tech Stack
- **Backend:** Python 3.14, FastAPI, SQLAlchemy (Async), Alembic
- **Database:** PostgreSQL 16 + `pgvector`
- **Cache:** Redis
- **AI / NLP:** Groq API (LLM), Hugging Face `sentence-transformers` (Embeddings)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (with `marked.js` for Markdown)

## 🏗️ Architecture
1. **Frontend:** User sends a message via HTTP POST (JSON).
2. **WAF:** Checks for prompt injection patterns and rate limits (Redis).
3. **RAG Pipeline:** Converts the query to a vector using Hugging Face, searches Postgres (`pgvector`) for relevant CVEs, and builds a context prompt.
4. **LLM:** Groq generates the final response using the context.
5. **Logs:** Uploaded files are scanned locally by Python rules, and the summary is sent to Groq for AI analysis.

## ⚙️ Quick Start
```bash
# Clone the repo
git clone https://github.com/felixotieno1011-art/felchat.git
cd felchat

# Set up environment variables
cp .env.example .env
# Add your GROQ_API_KEY and HF_TOKEN to .env

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Ingest CVEs (optional, requires HF token or local model)
python scripts/ingest_cves.py

# Start the server
uvicorn app.main:app --reload
