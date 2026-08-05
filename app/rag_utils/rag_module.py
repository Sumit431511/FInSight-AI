from pathlib import Path
import sqlite3
import os
import pandas as pd
from dotenv import load_dotenv

from app.config import get_data_dir


class SimpleDocument:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

try:
    from langchain_core.documents import Document
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_groq import ChatGroq
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_classic.chains.retrieval import create_retrieval_chain
    from langchain_cohere import CohereRerank
    from langchain_classic.retrievers import ContextualCompressionRetriever
except ImportError as exc:
    Document = None
    ChatPromptTemplate = None
    RecursiveCharacterTextSplitter = None
    Chroma = None
    HuggingFaceEmbeddings = None
    ChatGroq = None
    create_stuff_documents_chain = None
    create_retrieval_chain = None
    CohereRerank = None
    ContextualCompressionRetriever = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

if Document is None:
    Document = SimpleDocument

load_dotenv()

LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "RBAC-RAG"

embeddings = None
vectorstore = None
question_answering_chain = None
fallback_documents = []


class _FallbackRAGChain:
    def __init__(self, user_role: str):
        self.user_role = user_role.lower()

    def invoke(self, payload):
        question = payload.get("input", "")
        docs = [
            doc for doc in fallback_documents
            if _doc_is_visible_for_role(doc, self.user_role)
        ]

        if not docs:
            return {
                "answer": "No indexed documents were available for your role yet.",
                "context": [],
            }

        context_text = "\n\n".join(
            f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content[:800]}"
            for doc in docs
        )

        answer = (
            f"I found {len(docs)} relevant document(s) for your role.\n\n"
            f"{context_text}\n\n"
            f"Question: {question}"
        )

        return {"answer": answer, "context": docs}


def _doc_is_visible_for_role(doc, user_role: str) -> bool:
    role = (doc.metadata.get("role") or "").lower()
    if user_role == "c-level":
        return True
    if user_role == "general":
        return role in {"", "general"}
    return role in {"", user_role, "general"}


def _ensure_rag_dependencies():
    if _IMPORT_ERROR is not None:
        return True

    global embeddings, vectorstore, question_answering_chain

    if embeddings is None:
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    if vectorstore is None:
        vectorstore = Chroma(
            collection_name="my_collection",
            persist_directory=str(get_data_dir("chroma_db")),
            embedding_function=embeddings,
        )

    if question_answering_chain is None:
        system_prompt = (
            "You are an assistant for summarizing and answering queries from internal company documents.\n"
            "Always use the retrieved context to answer the query, even if partial.\n"
            "Do not guess. If data is not found, explain what you searched for.\n"
            "When responding:\n"
            "- Add **Source** from document metadata if possible.\n"
            "- Use headers\n"
            "- Use bullet points\n"
            "- For CSV-style data, format in table with two columns\n"
            "\n{context}"
        )
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        question_answering_chain = create_stuff_documents_chain(model, chat_prompt)

    return True


def embed_documents_to_vectorstore(docs):
    if not docs:
        return True

    normalized_docs = []
    if isinstance(docs, list):
        normalized_docs = docs
    else:
        normalized_docs = [docs]

    if _IMPORT_ERROR is not None:
        fallback_documents.extend(normalized_docs)
        print("Using in-memory fallback storage because optional RAG dependencies are unavailable.")
        return True

    if not _ensure_rag_dependencies():
        return False

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(normalized_docs)
    vectorstore.add_documents(splits)

    print("Documents embedded and saved to vectorstore.")
    print("Total documents:", len(vectorstore.get()["documents"]))
    return True

def load_file(filepath, role):
    ext = Path(filepath).suffix.lower()
    try:
        if ext == ".csv":
            df1 = pd.read_csv(filepath)
            documents = []
            for row in df1.to_dict(orient="records"):
                content = "\n".join(f"{k}: {v}" for k, v in row.items())
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"role": role.lower(), "source": Path(filepath).name}
                    )
                )
            return documents  

        elif ext in {".md", ".txt", ".text"}:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return [
                Document(
                    page_content=content,
                    metadata={"role": role.lower(), "source": Path(filepath).name}
                )
            ]
        else:
            return None

    except Exception as e:
        print(f"Failed to process {filepath}: {e}")
        return None


def run_indexer():
    db_path = str(get_data_dir("roles_docs.db"))
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, filepath, role FROM documents WHERE embedded = 0")

    all_docs = []

    for doc_id, path, role in c.fetchall():
        docs = load_file(path, role)
        if docs:
            if isinstance(docs, list):
                all_docs.extend(docs)
            else:
                all_docs.append(docs)

    if all_docs:
        embed_documents_to_vectorstore(all_docs)

        for doc_id, _, _ in c.fetchall():
            pass

        c.execute("SELECT id, filepath, role FROM documents WHERE embedded = 0")
        pending_docs = c.fetchall()
        for doc_id, _, _ in pending_docs:
            c.execute("UPDATE documents SET embedded = 1 WHERE id = ?", (doc_id,))
        conn.commit()

    conn.close()
    print(f"Indexed {len(all_docs)} document chunks.")

def wrap_with_reranker(retriever, cohere_api_key, top_n=4):
    _ensure_rag_dependencies()
    reranker = CohereRerank(cohere_api_key=cohere_api_key, top_n=top_n)
    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=retriever,
    )


def get_rag_chain(user_role: str, cohere_api_key: str = None):
    if _IMPORT_ERROR is not None:
        return _FallbackRAGChain(user_role)

    if not _ensure_rag_dependencies():
        return None

    user_role = user_role.lower()

    if user_role == "c-level":
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    elif user_role == "general":
        retriever = vectorstore.as_retriever(search_kwargs={
            "k": 4,
            "filter": {"role": "general"},
        })

    else:
        retriever = vectorstore.as_retriever(search_kwargs={
            "k": 4,
            "filter": {"role": {"$in": [user_role, "general"]}},
        })

    if cohere_api_key:
        print("Using cohere reranker")
        retriever = wrap_with_reranker(retriever, cohere_api_key)

    return create_retrieval_chain(retriever, question_answering_chain)
    """
    from langchain_core.runnables import RunnableLambda, RunnableMap

    extract_input = RunnableLambda(lambda x: x["input"])

    return RunnableMap({
        "context": extract_input | retriever,
        "answer": extract_input | retriever | question_answering_chain
    })"""


"""
# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    run_indexer() 
"""
    
"""
    user_role = "hr" 
    rag_chain = get_rag_chain(user_role)

    
    query = "give me Campaign Highlights from marketing summary."
    response = rag_chain.invoke({"input": query})

    print((response["answer"]))
    for doc in response.get("context", []):
        print(f"Source: {doc.metadata['source']}, Role: {doc.metadata.get('role')}")

"""

