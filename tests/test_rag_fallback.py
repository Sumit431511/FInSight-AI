from pathlib import Path

from app.rag_utils.rag_module import load_file, embed_documents_to_vectorstore


def test_load_file_returns_document_without_langchain_dependencies(tmp_path):
    sample_path = tmp_path / "sample.md"
    sample_path.write_text("# Finance Summary\nRevenue increased this quarter.", encoding="utf-8")

    docs = load_file(str(sample_path), "Finance")

    assert docs is not None
    assert len(docs) == 1
    assert docs[0].page_content.startswith("# Finance Summary")
    assert docs[0].metadata["source"] == sample_path.name
    assert docs[0].metadata["role"] == "finance"


def test_embed_documents_to_vectorstore_falls_back_when_langchain_missing(tmp_path):
    sample_path = tmp_path / "sample.txt"
    sample_path.write_text("RBAC access is granted to Finance users.", encoding="utf-8")

    docs = load_file(str(sample_path), "Finance")
    result = embed_documents_to_vectorstore(docs)

    assert result is True
