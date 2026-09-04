"""
Chat Endpoint Routes with Async Evaluation and Routing.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from app.auth.auth import get_current_user
from app.rag_evaluator.logger import log_chat
from app.rag_evaluator.metrics import build_metrics
from app.rag_evaluator.online_evaluator import evaluate_chat
from app.rag_utils.csv_query import ask_csv
from app.rag_utils.query_classifier import detect_query_type_llm
from app.rag_utils.rag_chain import ask_rag

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


def _async_evaluate_and_log(
    username: str,
    role: str,
    question: str,
    mode: str,
    result: dict,
    latency: float,
    fallback_used: bool,
    retrieved_docs: List[str],
    sources: List[str],
    retrieved_context: str,
):
    """Background task to run LLM evaluation and persist logs without blocking response."""
    try:
        evaluation = evaluate_chat(
            question=question,
            answer=result.get("answer", ""),
            retrieved_context=retrieved_context,
        )
    except Exception as e:
        print(f"Async evaluation error: {e}")
        evaluation = {
            "faithfulness": 0,
            "relevancy": 0,
            "context_recall": 0,
        }

    metrics = build_metrics(evaluation, latency, retrieved_docs)

    log_chat(
        username=username,
        role=role,
        question=question,
        mode=mode,
        answer=result.get("answer", ""),
        latency=latency,
        fallback=fallback_used,
        sql_query=result.get("sql"),
        retrieved_docs=retrieved_docs,
        sources=sources,
        evaluation=metrics,
    )


@router.post("/chat")
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    role = user["role"]
    username = user["username"]
    question = req.question

    start_time = time.perf_counter()
    mode = detect_query_type_llm(question)

    result = {}
    fallback_used = False

    if mode == "SQL":
        try:
            result = await ask_csv(
                question,
                role,
                username,
                return_sql=True,
            )
            if result.get("error") or not result.get("answer", "").strip():
                raise ValueError("SQL execution returned no valid data or error.")
        except Exception as e:
            print(f"SQL failed, falling back to RAG: {e}")
            result = await ask_rag(question, role)
            fallback_used = True
            mode = "SQL → RAG"

    elif mode == "RAG":
        result = await ask_rag(question, role)

    else:
        sql_result = await ask_csv(
            question,
            role,
            username,
            return_sql=True,
        )
        rag_result = await ask_rag(question, role)

        result = {
            "answer": (
                "## 📊 Structured Data\n\n"
                + sql_result.get("answer", "")
                + "\n\n---\n\n"
                + "## 📄 Retrieved Documents\n\n"
                + rag_result.get("answer", "")
            ),
            "context": rag_result.get("context", []),
        }
        if "sql" in sql_result:
            result["sql"] = sql_result["sql"]

    latency = round((time.perf_counter() - start_time) * 1000, 2)

    # Extract source metadata
    retrieved_docs = []
    source_names = []
    citations = []
    contexts = []

    for doc in result.get("context", []):
        if isinstance(doc, dict):
            source = doc.get("metadata", {}).get("source", "Unknown")
            page_content = doc.get("page_content", "")
        else:
            source = getattr(doc, "metadata", {}).get("source", "Unknown")
            page_content = getattr(doc, "page_content", "")

        retrieved_docs.append(source)
        source_names.append(source)
        citations.append(
            {
                "source": source,
                "document_id": doc.get("metadata", {}).get("document_id") if isinstance(doc, dict) else getattr(doc, "metadata", {}).get("document_id"),
                "page": doc.get("metadata", {}).get("page") if isinstance(doc, dict) else getattr(doc, "metadata", {}).get("page"),
            }
        )
        contexts.append(page_content)

    retrieved_context = "\n\n".join(contexts)

    # Trigger async evaluation and logging in background
    background_tasks.add_task(
        _async_evaluate_and_log,
        username,
        role,
        question,
        mode,
        result,
        latency,
        fallback_used,
        retrieved_docs,
        source_names,
        retrieved_context,
    )

    return {
        "user": username,
        "role": role,
        "mode": mode,
        "fallback": fallback_used,
        "latency": latency,
        "confidence": 90.0,  # Fast preliminary confidence response while background task evaluates
        "answer": result.get("answer", ""),
        "sources": citations,
        **({"sql": result["sql"]} if "sql" in result else {}),
    }
