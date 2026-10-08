from src.rag.loader import KnowledgeLoader
from src.core.config import KNOWLEDGE_PATH
import pytest


@pytest.fixture(scope="module")
def documents():
    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    return loader.load_all_documents()


def test_loader_loads_documents(documents) -> None:
    assert len(documents) > 0, "The loader did not load any documents."


def test_loader_generates_unique_doc_ids(documents) -> None:
    doc_ids = [doc.doc_id for doc in documents]

    assert len(doc_ids) == len(set(doc_ids)), "Duplicate doc_ids were found."


def test_all_documents_have_required_enriched_metadata(documents) -> None:

    for doc in documents:
        assert "type" in doc.metadata, f"{doc.doc_id} is missing 'type'."
        assert "source" in doc.metadata, f"{doc.doc_id} is missing 'source'."
        assert "title" in doc.metadata, f"{doc.doc_id} is missing 'title'."
        assert "filename" in doc.metadata, f"{doc.doc_id} is missing 'filename'."


def test_all_documents_have_non_empty_content(documents) -> None:

    for doc in documents:
        assert doc.content.strip() != "", f"{doc.doc_id} has empty content."


def test_metadata_block_is_removed_from_content(documents) -> None:

    for doc in documents:
        assert "## Metadata" not in doc.content, (
            f"{doc.doc_id} still contains the metadata block in content."
        )


def test_document_type_matches_allowed_values(documents) -> None:
    valid_types = {"domain", "subdomain", "product", "cross_doc"}

    for doc in documents:
        assert doc.metadata['type'] in valid_types, (
            f"{doc.doc_id} has invalid type '{doc.metadata['type']}'."
        )


def test_document_title_is_not_empty(documents) -> None:

    for doc in documents:
        assert doc.metadata["title"].strip() != "", (
            f"{doc.doc_id} has an empty title."
        )


def test_document_source_points_to_markdown_file(documents) -> None:

    for doc in documents:
        assert doc.metadata["source"].endswith(".md"), (
            f"{doc.doc_id} source is not a markdown file."
        )
