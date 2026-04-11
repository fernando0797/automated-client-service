from src.core.config import KNOWLEDGE_PATH
from src.rag.loader import KnowledgeLoader
from src.rag.chunking import Chunker
from src.rag.embeddings import Embedder
import pytest


@pytest.fixture(scope="module")
def chunks():
    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    documents = loader.load_all_documents()

    chunker = Chunker(documents)
    return chunker.chunk_all_documents()


@pytest.fixture(scope="module")
def embeddings(chunks):
    embedder = Embedder()
    return embedder.embed_chunks(chunks)


def test_embeddings_not_empty(embeddings):
    assert len(embeddings) > 0


def test_length_embeddings_matches_chunks(chunks, embeddings):
    assert len(chunks) == len(embeddings)


def test_embeddings_have_same_dimension(embeddings):
    first_dimension = len(embeddings[0])

    for embedding in embeddings:
        assert len(embedding) == first_dimension


def test_embedding_dimension_is_greater_than_zero(embeddings):
    assert len(embeddings[0]) > 0


def test_empty_texts_returns_empty_list():
    embedder = Embedder()
    embeddings = embedder.embed_texts([])

    assert embeddings == []


def test_empty_chunks_returns_empty_list():
    embedder = Embedder()
    embeddings = embedder.embed_chunks([])

    assert embeddings == []
