import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "chat_logs.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================
# Overall Statistics
# ============================================

def overall_summary():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT confidence,
               latency,
               mode,
               fallback
        FROM chat_logs
    """)

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return {
            "total_queries": 0
        }

    confidences = []
    latencies = []

    sql_count = 0
    rag_count = 0
    fallback_count = 0

    for confidence, latency, mode, fallback in rows:

        if confidence is not None:
            confidences.append(confidence)

        if latency is not None:
            latencies.append(latency)

        if mode == "SQL":
            sql_count += 1
        else:
            rag_count += 1

        if fallback:
            fallback_count += 1

    return {

        "total_queries": len(rows),

        "avg_confidence":
            round(sum(confidences)/len(confidences),2)
            if confidences else 0,

        "avg_latency":
            round(sum(latencies)/len(latencies),2)
            if latencies else 0,

        "sql_queries": sql_count,

        "rag_queries": rag_count,

        "fallback_rate":
            round(
                fallback_count/len(rows)*100,
                2
            )

    }
# ============================================
# Role Summary
# ============================================

def role_summary():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT role,

           COUNT(*),

           AVG(confidence),

           AVG(latency)

    FROM chat_logs

    GROUP BY role

    """)

    rows = cursor.fetchall()

    conn.close()

    output = []

    for row in rows:

        output.append({

            "role": row[0],

            "queries": row[1],

            "confidence": round(row[2],2) if row[2] else 0,

            "latency": round(row[3],2) if row[3] else 0,

        })

    return output
# ============================================
# Document Usage
# ============================================

def document_usage():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT retrieved_docs

    FROM chat_logs

    """)

    rows = cursor.fetchall()

    conn.close()

    counts = {}

    for row in rows:

        if not row[0]:
            continue

        try:

            docs = json.loads(row[0])

        except:

            continue

        for doc in docs:

            counts[doc] = counts.get(doc,0)+1

    return sorted(

        counts.items(),

        key=lambda x:x[1],

        reverse=True

    )
# ============================================
# Failed Queries
# ============================================

def failed_queries(limit=10):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT

    question,

    confidence,

    role,

    mode

    FROM chat_logs

    ORDER BY confidence ASC

    LIMIT ?

    """,(limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows