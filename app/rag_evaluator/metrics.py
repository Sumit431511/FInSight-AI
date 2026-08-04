"""
Production evaluation metrics.

These metrics are independent of the LLM evaluator.
"""

# ==========================================
# Confidence Score
# ==========================================

def calculate_confidence(
    faithfulness: float,
    relevancy: float,
    context_recall: float,
):
    """
    Weighted confidence score.
    Returns a value between 0 and 100.
    """

    confidence = (
        faithfulness * 0.45 +
        relevancy * 0.35 +
        context_recall * 0.20
    ) * 100

    return round(confidence, 2)


# ==========================================
# Hallucination Score
# ==========================================

def hallucination_score(
    faithfulness: float,
):
    """
    Lower faithfulness means higher hallucination.
    """

    score = (1 - faithfulness) * 100

    return round(score, 2)


# ==========================================
# Latency Rating
# ==========================================

def latency_rating(
    latency_ms: float,
):
    """
    Human-readable latency rating.
    """

    if latency_ms < 500:
        return "Excellent"

    elif latency_ms < 1200:
        return "Good"

    elif latency_ms < 2500:
        return "Average"

    return "Slow"


# ==========================================
# Source Coverage
# ==========================================

def source_coverage(
    retrieved_docs,
):
    """
    Number of retrieved documents.
    """

    return len(retrieved_docs)


# ==========================================
# Retriever Hit Rate
# ==========================================

def retriever_hit_rate(
    retrieved_docs,
):
    """
    Placeholder implementation.

    Later we'll calculate this using similarity scores.
    """

    if not retrieved_docs:
        return 0.0

    return 100.0


# ==========================================
# Performance Grade
# ==========================================

def performance_grade(
    confidence: float,
):
    """
    Convert confidence score into a grade.
    """

    if confidence >= 95:
        return "A+"

    elif confidence >= 90:
        return "A"

    elif confidence >= 80:
        return "B"

    elif confidence >= 70:
        return "C"

    elif confidence >= 60:
        return "D"

    return "F"


# ==========================================
# Overall Metrics Builder
# ==========================================

def build_metrics(
    evaluation: dict,
    latency: float,
    retrieved_docs: list,
):
    """
    Builds all production metrics used
    throughout the dashboard.
    """

    faithfulness = evaluation.get(
        "faithfulness",
        0.0,
    )

    relevancy = evaluation.get(
        "relevancy",
        0.0,
    )

    context_recall = evaluation.get(
        "context_recall",
        0.0,
    )

    confidence = calculate_confidence(
        faithfulness,
        relevancy,
        context_recall,
    )

    return {

        # Core Evaluation Metrics
        "faithfulness": faithfulness,

        "relevancy": relevancy,

        "context_recall": context_recall,

        # Derived Metrics
        "confidence": confidence,

        "performance": performance_grade(
            confidence
        ),

        "hallucination": hallucination_score(
            faithfulness
        ),

        "latency_ms": latency,

        "latency_rating": latency_rating(
            latency
        ),

        "source_count": source_coverage(
            retrieved_docs
        ),

        "retriever_hit_rate": retriever_hit_rate(
            retrieved_docs
        ),
    }