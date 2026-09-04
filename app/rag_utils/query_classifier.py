import os
from dotenv import load_dotenv
from app.config import get_groq_model

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_groq import ChatGroq
except ImportError:
    ChatPromptTemplate = None
    ChatGroq = None

load_dotenv()

llm = None
classifier = None

if ChatGroq is not None and ChatPromptTemplate is not None:
    llm = ChatGroq(
        model=get_groq_model(),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    classification_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a classifier that decides if a user's question should be handled by:

SQL
or
RAG

Rules:

Return SQL if the question involves:
- count
- average
- sum
- total
- maximum
- minimum
- top
- bottom
- filter
- employee details
- tabular information
- database lookup

Return RAG if the question involves:
- summaries
- policies
- documents
- explanations
- company procedures
- reports
- markdown documents

Return ONLY one word:

SQL

or

RAG
"""
        ),
        ("human", "{question}"),
    ])

    classifier = classification_prompt | llm


def detect_query_type_llm(question: str) -> str:
    if classifier is None:
        return "RAG"

    response = classifier.invoke({"question": question})
    return response.content.strip().upper()
