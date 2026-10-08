from src.core.models import KnowledgeChunk
from src.rag.loader import KnowledgeLoader
from src.core.config import KNOWLEDGE_PATH
from src.rag.chunking import Chunker
import pytest


@pytest.fixture(scope="module")
def chunks():
    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    documents = loader.load_all_documents()

    chunker = Chunker(documents)
    chunks = chunker.chunk_all_documents()
    return chunks


def test_chunks_is_list(chunks) -> None:
    assert isinstance(chunks, list)


def test_chunks_contains_KnowledgeChunk(chunks) -> None:
    for chunk in chunks:
        assert isinstance(chunk, KnowledgeChunk)


def test_chunks_not_empty(chunks) -> None:
    assert len(chunks) > 0


def test_filename_notin_chunk_metadata(chunks) -> None:
    for chunk in chunks:
        assert "filename" not in chunk.metadata


def test_chunk_index_in_chunk_metadata(chunks) -> None:
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata


def test_chunk_id_not_empty(chunks) -> None:
    for chunk in chunks:
        assert chunk.chunk_id.strip() != ""


def test_parent_doc_id_not_empty(chunks) -> None:
    for chunk in chunks:
        assert chunk.parent_doc_id.strip() != ""


def test_chunk_content_not_empty(chunks) -> None:
    for chunk in chunks:
        assert chunk.content.strip() != ""


def test_chunk_id_contains_parent_doc_id(chunks) -> None:
    for chunk in chunks:
        assert chunk.parent_doc_id in chunk.chunk_id


def test_chunk_id_contains_chunk_suffix(chunks) -> None:
    for chunk in chunks:
        assert "__chunk" in chunk.chunk_id


def test_chunk_index_is_integer(chunks) -> None:
    for chunk in chunks:
        assert isinstance(chunk.metadata["chunk_index"], int)


def test_chunk_indexes_are_valid_per_document(chunks) -> None:
    chunks_by_doc = {}

    for chunk in chunks:
        parent_doc_id = chunk.parent_doc_id
        chunk_index = chunk.metadata["chunk_index"]

        if parent_doc_id not in chunks_by_doc:
            chunks_by_doc[parent_doc_id] = []

        chunks_by_doc[parent_doc_id].append(chunk_index)

    for indexes in chunks_by_doc.values():
        sorted_indexes = sorted(indexes)
        expected_indexes = list(range(len(sorted_indexes)))
        assert sorted_indexes == expected_indexes
