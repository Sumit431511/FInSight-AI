import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "chat_logs.db"


def get_dashboard_data():

    conn = sqlite3.connect(DB_PATH)

    # -------------------------------
    # Load chat history
    # -------------------------------

    history = pd.read_sql_query(

        """
        SELECT 
        id,
        timestamp,
        username,
        role,
        question,
        mode,
        fallback,
        latency_ms,

        faithfulness,
        relevancy,
        context_recall,
        confidence,
        hallucination,
        retriever_hit_rate,
        source_count
        FROM chat_logs
        ORDER BY id DESC
        """,

        conn

    )

    # -------------------------------
    # Empty database
    # -------------------------------

    if history.empty:

        conn.close()

        return {

            "overview": {

                "total_queries": 0,

                "avg_confidence": 0,

                "avg_faithfulness": 0,

                "avg_latency": 0,

                "hallucination_rate": 0,

                "sql_ratio": 0,

                "rag_ratio": 0,

                "fallback_rate": 0,

                "avg_sources": 0,

            },

            "history": []

        }

    # -------------------------------
    # Overview
    # -------------------------------

    total_queries = len(history)

    avg_confidence = history["confidence"].mean()

    avg_faithfulness = history["faithfulness"].mean()

    avg_latency = history["latency_ms"].mean()

    hallucination_rate = history["hallucination"].mean()

    avg_sources = history["source_count"].mean()

    sql_queries = history["mode"].astype(str).str.contains("SQL").sum()

    rag_queries = history["mode"].astype(str).str.contains("RAG").sum()

    fallback_queries = history["fallback"].sum()

    sql_ratio = round((sql_queries / total_queries) * 100, 2)

    rag_ratio = round((rag_queries / total_queries) * 100, 2)

    fallback_rate = round((fallback_queries / total_queries) * 100, 2)

    conn.close()

    return {

        "overview": {

            "total_queries": total_queries,

            "avg_confidence": round(avg_confidence, 2),

            "avg_faithfulness": round(avg_faithfulness, 2),

            "avg_latency": round(avg_latency, 2),

            "hallucination_rate": round(hallucination_rate, 2),

            "sql_ratio": sql_ratio,

            "rag_ratio": rag_ratio,

            "fallback_rate": fallback_rate,

            "avg_sources": round(avg_sources, 2),

        },

        "history": history.to_dict(orient="records")

    }