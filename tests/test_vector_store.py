import pytest

from src.core.config import KNOWLEDGE_PATH
from src.rag.loader import KnowledgeLoader
from src.rag.chunking import Chunker
from src.rag.embeddings import Embedder
from src.rag.vector_store import VectorStore


@pytest.fixture(scope="module")
def chunks():
    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    documents = loader.load_all_documents()

    chunker = Chunker(documents)
    return chunker.chunk_all_documents()


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


@pytest.fixture(scope="module")
def chunk_embeddings(chunks, embedder):
    return embedder.embed_chunks(chunks)


@pytest.fixture(scope="module")
def vector_store(chunks, chunk_embeddings):
    store = VectorStore()
    store.build_index(chunk_embeddings, chunks)
    return store


def test_index_is_built(vector_store):
    assert vector_store.index is not None


def test_index_dimension_is_set(vector_store):
    assert vector_store.dimension is not None
    assert vector_store.dimension > 0


def test_number_of_stored_chunks_matches_input(vector_store, chunks):
    assert len(vector_store.chunks) == len(chunks)


def test_search_returns_k_results(vector_store, embedder):
    query = "password reset help"
    query_embedding = embedder.embed_texts([query])[0]

    results = vector_store.search(query_embedding, k=3)

    assert len(results) == 3


def test_search_returns_knowledge_chunks(vector_store, embedder):
    query = "password reset help"
    query_embedding = embedder.embed_texts([query])[0]

    results = vector_store.search(query_embedding, k=3)

    for result in results:
        assert result.__class__.__name__ == "KnowledgeChunk"


def test_search_with_scores_returns_k_results(vector_store, embedder):
    query = "password reset help"
    query_embedding = embedder.embed_texts([query])[0]

    results = vector_store.search_with_scores(query_embedding, k=3)

    assert len(results) == 3


def test_search_with_scores_returns_chunk_and_score(vector_store, embedder):
    query = "password reset help"
    query_embedding = embedder.embed_texts([query])[0]

    results = vector_store.search_with_scores(query_embedding, k=3)

    for chunk, score in results:
        assert chunk.__class__.__name__ == "KnowledgeChunk"
        assert isinstance(score, float)


def test_search_raises_error_if_index_not_built(embedder):
    store = VectorStore()
    query = "password reset help"
    query_embedding = embedder.embed_texts([query])[0]

    with pytest.raises(ValueError, match="The FAISS index has not been built yet."):
        store.search(query_embedding, k=3)


def test_build_index_raises_error_if_embeddings_empty(chunks):
    store = VectorStore()

    with pytest.raises(ValueError, match="Embeddings list cannot be empty."):
        store.build_index([], chunks)


def test_build_index_raises_error_if_lengths_do_not_match(chunks, chunk_embeddings):
    store = VectorStore()

    with pytest.raises(ValueError, match="The number of embeddings must match the number of chunks."):
        store.build_index(chunk_embeddings[:-1], chunks)
