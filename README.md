# 🚀 FinSight – Enterprise AI Assistant with Hybrid RAG, SQL Agent & RBAC

FinSight is an enterprise-grade AI assistant that combines **Retrieval-Augmented Generation (RAG)**, **Natural Language to SQL**, and **Role-Based Access Control (RBAC)** to securely answer both structured and unstructured business queries.

The system automatically classifies user queries, routes them to the appropriate engine (SQL or RAG), evaluates every AI response using an LLM evaluator, and provides an admin dashboard for monitoring AI performance.

---

## ✨ Features

- 🔐 JWT Authentication & Role-Based Access Control (RBAC)
- 🤖 Hybrid Query Routing (SQL + RAG)
- 📊 Natural Language to SQL using DuckDB
- 📄 Enterprise Document Search with ChromaDB
- 🎯 Automatic Query Classification
- 🔄 SQL → RAG Fallback Mechanism
- 📈 AI Evaluation Dashboard
- 📚 Multi-document Upload & Indexing
- ⚡ Groq Llama 3.3 70B Integration
- 🧪 Automated Testing using Pytest & Playwright

---

## 🏗️ System Architecture

```text
                 User
                  │
                  ▼
          JWT Authentication
                  │
                  ▼
        Query Classification
        ┌──────────┴──────────┐
        ▼                     ▼
   SQL Engine             RAG Engine
   (DuckDB)            (ChromaDB + LLM)
        │                     │
        └──────────┬──────────┘
                   ▼
             Response Generator
                   │
                   ▼
           AI Evaluation Engine
                   │
                   ▼
          Admin Analytics Dashboard
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM | Groq (Llama 3.3 70B) |
| Framework | LangChain |
| Vector Database | ChromaDB |
| SQL Engine | DuckDB |
| Database | SQLite |
| Authentication | JWT |
| Embeddings | HuggingFace |
| Reranker | Cohere |
| Testing | Pytest, Playwright |

---

## 📊 AI Evaluation Metrics

Every RAG response is automatically evaluated using an LLM.

- ✅ Faithfulness
- ✅ Relevancy
- ✅ Context Recall
- ✅ Confidence Score
- ✅ Hallucination Rate
- ✅ Retriever Hit Rate
- ✅ Source Count
- ✅ Response Latency

---

## 👥 Supported Roles

- C-Level
- HR
- Finance
- Engineering
- Operations

Each role can access only authorized documents using RBAC.

---

## 📂 Project Structure

```text
RBAC-Project/
│
├── app/
│   ├── auth/
│   ├── rag_utils/
│   ├── rag_evaluator/
│   ├── main.py
│
├── docs/
├── uploads/
├── chroma_db/
├── ui.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

Clone the repository

```bash
git clone <repository-url>
cd RBAC-Project
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

```bash
# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_api_key
GROQ_MODEL=openai/gpt-oss-120b
COHERE_API_KEY=your_api_key
LANGCHAIN_API_KEY=your_api_key
JWT_SECRET_KEY=your_secret_key
SECRET_KEY=your_secret_key
COOKIE_SECRET_KEY=another-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
API_URL=http://localhost:8000
PROJECT_ROOT=.
PORT=8000
DEFAULT_ADMIN_PASSWORD=choose-a-strong-first-admin-password
ENVIRONMENT=development
# Leave empty locally. Set this to a persistent disk location in deployment.
DATA_DIR=
```

> For deployment, make sure the same variables are set in the hosting environment and that the app has write access to the project data folders for SQLite and Chroma storage.

### Basic Python deployment

Run FastAPI and Streamlit as separate Python services. The Streamlit service must
use the public HTTPS URL of the FastAPI service as `API_URL`; the API must use the
public HTTPS URL of Streamlit as `FRONTEND_URL`.

The API service needs a persistent writable `DATA_DIR`. It stores SQLite, DuckDB,
ChromaDB, uploads, and evaluation logs there. Do not use an ephemeral service
filesystem for this directory: data and indexes would disappear after a restart.

---

## ▶️ Run the Project

Start the backend

```bash
uvicorn app.main:app --reload
```

Start the frontend

```bash
streamlit run app/ui.py
```

---

## 📈 Admin Dashboard

The dashboard provides:

- AI Evaluation Metrics
- Query History
- Confidence Scores
- Latency Monitoring
- SQL vs RAG Analytics
- Hallucination Detection
- Role-wise Query Statistics

---

## 💬 Sample Queries

### SQL Queries

- Show employee salary details
- List all departments
- Show finance reports

### RAG Queries

- Explain leave policy
- What is the engineering onboarding process?
- Summarize company security guidelines

---

## 🚀 Future Enhancements

- PostgreSQL Support
- Redis Caching
- Multi-Agent Workflow
- Real-time Monitoring
- Advanced Retriever Analytics
- Docker Deployment
- CI/CD Pipeline
- Kubernetes Deployment

---

## 📄 License

This project is developed for educational and research purposes.
