import json
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.config import get_groq_model

from .prompts import RAG_EVALUATION_PROMPT

load_dotenv()

llm = ChatGroq(
    model=get_groq_model(),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)


def evaluate_answer(
    question: str,
    answer: str,
    retrieved_context: str,
    ground_truth: str,
):
    """
    Evaluate a generated answer using an LLM.
    Returns parsed JSON metrics.
    """

    prompt = RAG_EVALUATION_PROMPT.format(
        question=question,
        context=retrieved_context,
        answer=answer,
        ground_truth=ground_truth,
    )

    response = llm.invoke(prompt)

    text = response.content.strip()

    try:
        return json.loads(text)

    except Exception:

        return {

            "faithfulness": 0,

            "relevancy": 0,

            "context_recall": 0,

            "reason": "Invalid JSON returned by evaluator.",

            "raw_response": text,

        }
