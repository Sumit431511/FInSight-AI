from .rag_module import get_rag_chain


async def ask_rag(
    question: str,
    role: str,
    cohere_api_key: str | None = None,
) -> dict:
    """
    Execute the RBAC-aware RAG pipeline and return
    both the answer and retrieved source documents.
    """

    rag_chain = get_rag_chain(
        user_role=role,
        cohere_api_key=cohere_api_key,
    )

    if rag_chain is None:
        return {
            "answer": (
                "RAG is currently unavailable in this deployment because the optional AI dependencies "
                "did not load successfully. The app is still available for authentication and basic browsing."
            ),
            "context": [],
        }

    result = rag_chain.invoke(
        {
            "input": question,
        }
    )

    documents = []

    for doc in result.get("context", []):
        documents.append(
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
        )

    return {
        "answer": result.get("answer", ""),
        "context": documents,
    }