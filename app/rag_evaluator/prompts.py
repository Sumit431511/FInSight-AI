"""
All prompts used by the evaluation framework.
"""


# ===============================================
# Question Generation Prompt
# ===============================================

QUESTION_GENERATION_PROMPT = """
You are an expert dataset generator.

Given the following document chunk, generate ONE factual question that can
be answered ONLY using the provided text.

Document:

{context}

Return ONLY the question.
"""


# ===============================================
# RAG Evaluation Prompt
# ===============================================

RAG_EVALUATION_PROMPT = """
You are an expert evaluator for Retrieval-Augmented Generation systems.

Evaluate the generated answer using the retrieved context.

Question:
{question}

Retrieved Context:
{context}

Generated Answer:
{answer}

Ground Truth:
{ground_truth}

Return ONLY valid JSON.

Required JSON format:

{{
    "faithfulness":0.0,
    "relevancy":0.0,
    "context_recall":0.0,
    "reason":"short explanation"
}}

Scoring Guide:

Faithfulness
0 = hallucinated
1 = completely grounded

Relevancy
0 = irrelevant
1 = fully answers the question

Context Recall
0 = retrieved context misses ground truth
1 = retrieved context fully covers ground truth
"""