import json
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)


def evaluate_chat(
    question: str,
    answer: str,
    retrieved_context: str,
 ):
    """
    Live RAG evaluation.

    This evaluates a real user conversation.

    No ground truth is required.
    """

    prompt = f"""
    You are an expert evaluator for Enterprise Retrieval-Augmented Generation systems.

   Evaluate ONLY using the retrieved context.

Question

{question}

------------------------------------

Retrieved Context

{retrieved_context}

------------------------------------

Generated Answer

{answer}

------------------------------------

Return ONLY valid JSON.

{{
    "faithfulness":0.0,
    "relevancy":0.0,
    "context_recall":0.0,
    "reason":"..."
}}

Scoring

Faithfulness

0 = hallucinated

1 = fully grounded

Relevancy

0 = irrelevant

1 = completely answers question

Context Recall

0 = retrieved context is poor

1 = retrieved context fully supports answer

Return ONLY JSON.
"""

    import json
    import re

    response = llm.invoke(prompt)

    text = response.content.strip()

    print("\n========== GROQ RAW RESPONSE ==========")
    print(text)
    print("=======================================\n")

    # Remove markdown fences
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text).strip()

    # Extract JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:

        try:

            return json.loads(match.group())

        except Exception as e:

            print(e)

    print("Unable to parse evaluator JSON.")

    return {

        "faithfulness":0,

        "relevancy":0,

        "context_recall":0,

        "reason":"Invalid JSON",

        "raw_response":text

    }