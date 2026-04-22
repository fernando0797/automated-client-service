import pytest

from src.core.models import KnowledgeChunk, RetrievalResult
from src.core.request_models import Ticket
from src.core.config import KNOWLEDGE_PATH
from src.rag.loader import KnowledgeLoader
from src.rag.chunking import Chunker
from src.rag.embeddings import Embedder
from src.rag.vector_store import VectorStore
from src.rag.retriever import Retriever


@pytest.fixture(scope="module")
def chunks():
    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    documents = loader.load_all_documents()

    chunker = Chunker(documents)
    chunks = chunker.chunk_all_documents()
    return chunks


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


@pytest.fixture(scope="module")
def vector_store():
    return VectorStore()


@pytest.fixture(scope="module")
def retriever(chunks, embedder, vector_store):
    return Retriever(chunks, embedder, vector_store)


@pytest.fixture(scope="module")
def good_ticket():
    return Ticket(
        description=(
            "I am having trouble with the initial setup of my Amazon Echo. "
            "The setup wizard starts, but one of the required steps fails, "
            "which means I cannot finish the configuration and begin using "
            "the product normally. Please provide step-by-step guidance to "
            "complete the setup. The issue is currently blocking normal use, "
            "so I need an urgent solution."
        ),
        ticket_id="2",
        source="database",
        domain="product_support",
        subdomain="product_setup",
        product="amazon_echo",
    )


@pytest.fixture(scope="module")
def bad_ticket():
    return Ticket(
        description=(
            "I am having trouble with the initial setup of my GoPro Hero. "
            "The setup wizard starts, but one of the required steps fails, "
            "which means I cannot finish the configuration and begin using "
            "the product normally. Please provide step-by-step guidance to "
            "complete the setup. The issue is currently blocking normal use, "
            "so I need an urgent solution."
        ),
        ticket_id="2",
        source="database",
        domain="null",
        subdomain="null",
        product="null",
    )


# 1. INITIALIZATION TESTS

def test_chunks_exist(retriever):
    assert retriever.chunks is not None


def test_embedder_exist(retriever):
    assert retriever.embedder is not None


def test_vectorstore_exist(retriever):
    assert retriever.vectorstore is not None


def test_embeddings_exist(retriever):
    assert retriever.embeddings is not None


def test_vectorstore_index_exist(retriever):
    assert retriever.vectorstore.index is not None


def test_chunkid_to_index_mapper_exist(retriever):
    assert retriever.chunk_id_to_index is not None


def test_number_of_embeddings_equals_number_of_chunks(retriever):
    assert len(retriever.chunks) == len(retriever.embeddings)


def test_chunkid_to_index_maps_each_chunk_to_correct_position(retriever):
    assert len(retriever.chunks) == len(retriever.chunk_id_to_index)

    for expected_index, chunk in enumerate(retriever.chunks):
        assert chunk.chunk_id in retriever.chunk_id_to_index

        mapped_index = retriever.chunk_id_to_index[chunk.chunk_id]
        assert expected_index == mapped_index
        assert chunk.chunk_id == retriever.chunks[mapped_index].chunk_id


# _filter_chunks TESTS

def test_filter_chunks_returns_list(retriever, good_ticket):
    results = retriever._filter_chunks(good_ticket)
    assert isinstance(results, list)


def test_filter_chunks_returns_KnowledgeChunk(retriever, good_ticket):
    results = retriever._filter_chunks(good_ticket)
    assert len(results) > 0
    for result in results:
        assert isinstance(result, KnowledgeChunk)


def test_chunk_domain_is_equivalent_to_ticket_domain(retriever, good_ticket):
    chunks = retriever._filter_chunks(good_ticket)
    domain_list = []
    for chunk in chunks:
        if chunk.type == "domain":
            domain_list.append(chunk)
    assert len(domain_list) > 0
    for chunk in domain_list:
        assert chunk.metadata["domain"] == good_ticket.domain


def test_chunk_subdomain_is_equivalent_to_ticket_subdomain(retriever, good_ticket):
    chunks = retriever._filter_chunks(good_ticket)
    subdomain_list = []
    for chunk in chunks:
        if chunk.type == "subdomain":
            subdomain_list.append(chunk)
    assert len(subdomain_list) > 0
    for chunk in subdomain_list:
        assert chunk.metadata["subdomain"] == good_ticket.subdomain


def test_chunk_product_is_equivalent_to_ticket_product(retriever, good_ticket):
    chunks = retriever._filter_chunks(good_ticket)
    product_list = []
    for chunk in chunks:
        if chunk.type == "product":
            product_list.append(chunk)
    assert len(product_list) > 0
    for chunk in product_list:
        assert chunk.metadata["product"] == good_ticket.product


def test_chunk_cross_is_equivalent_to_ticket_subdomain_and_product(retriever, good_ticket):
    chunks = retriever._filter_chunks(good_ticket)
    cross_list = []
    for chunk in chunks:
        if chunk.type == "cross_doc":
            cross_list.append(chunk)
    assert len(cross_list) > 0
    for chunk in cross_list:
        assert chunk.metadata["subdomain"] == good_ticket.subdomain
        assert chunk.metadata["product"] == good_ticket.product


def test_empty_list_when_no_filters_match(retriever, bad_ticket):
    chunks = retriever._filter_chunks(bad_ticket)
    assert chunks == []

# _embed_query TESTS


def test_embedding_not_none(retriever, good_ticket):
    query = retriever._build_query(good_ticket)
    query_embedding = retriever._embed_query(query)
    assert query_embedding is not None


def test_embedding_has_same_length_as_index(retriever, good_ticket):
    query = retriever._build_query(good_ticket)
    query_embedding = retriever._embed_query(query)
    assert len(query_embedding) == retriever.vectorstore.dimension

# filter_retrieve TESTS


def test_filter_retrieve_returns_list(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket)
    assert isinstance(results, list)


def test_filter_retrieve_all_elements_are_RetrievalResult(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket)
    for result in results:
        assert isinstance(result, RetrievalResult)


def test_all_elements_contain_filter_source(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket)
    for result in results:
        assert result.source == "filter"


def test_returns_empty_list_when_no_filters_match(retriever, bad_ticket):
    results = retriever.filter_retrieve(bad_ticket)
    assert results == []


def test_all_chunks_retrieved_when_k_is_none(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket, None)
    results2 = retriever._filter_chunks(good_ticket)
    assert len(results) == len(results2)


def test_returns_all_filtered_chunks_when_k_is_too_big(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket, 9999)
    results2 = retriever._filter_chunks(good_ticket)
    assert len(results) == len(results2)


def test_function_doesnt_break_with_negative_k(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket, -5)
    results2 = retriever._filter_chunks(good_ticket)
    assert isinstance(results, list)
    assert len(results) <= len(results2)


def test_filter_retrieve_has_distance_in_ascending_order(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket)
    distance_list = []
    for result in results:
        distance_list.append(result.distance)
    assert distance_list == sorted(distance_list)


def test_results_contain_knowledgechunks(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket)
    for result in results:
        assert isinstance(result.chunk, KnowledgeChunk)

# semantic_retrieve TESTS


def test_semantic_retrieve_returns_list(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket)
    assert isinstance(results, list)


def test_semantic_retrieve_list_contains_RetrievalResult(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket)
    for result in results:
        assert isinstance(result, RetrievalResult)


def test_semantic_retrieve_list_contains_semantic_source(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket)
    for result in results:
        assert result.source == "semantic"


def test_semantic_retrieve_list_is_never_larger_than_k(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, 3)
    k = 3
    assert len(results) <= k


def test_semantic_retrieve_list_able_to_cut_when_k_too_large(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, 9999999)
    k = 9999999
    assert len(results) < k
    assert len(results) == len(retriever.chunks)


def test_semantic_retrieve_list_doesnt_break_with_nonpositive_k_and_defaults_to_5(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, -5)
    assert len(results) <= 5


def test_semantic_retrieve_list_ordered_by_distance(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, 15)
    distance_list = []
    for result in results:
        distance_list.append(result.distance)
    assert distance_list == sorted(distance_list)


# hybrid_retrieve TESTS

def test_hybrid_retrieve_returns_list(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    assert isinstance(results, list)


def test_hybrid_retrieve_list_contains_RetrievalResult(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    for result in results:
        assert isinstance(result, RetrievalResult)


def test_hybrid_retrieve_list_length_never_larger_than_k(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket, 3)
    k = 3
    assert len(results) <= k


def test_hybrid_retrieve_list_doesnt_break_with_nonpositive_k_and_defaults_to_5(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket, -4)
    assert len(results) <= 5


def test_hybrid_retrieve_list_sorted_by_distance(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    distance_list = []
    for result in results:
        distance_list.append(result.distance)
    assert distance_list == sorted(distance_list)


def test_hybrid_retrieve_list_has_no_duplicates(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    chunkids = []
    for result in results:
        chunkids.append(result.chunk.chunk_id)
    assert len(chunkids) == len(set(chunkids))


def test_hybrid_retrieve_contains_hybrid_source(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    for result in results:
        assert result.source in {"hybrid", "semantic", "filter"}


def test_hybrid_retrieve_marks_duplicate_chunk_as_hybrid(monkeypatch, retriever, good_ticket):
    chunk = retriever.chunks[0]

    filter_results = [RetrievalResult(
        chunk=chunk, distance=0.8, source="filter")]
    semantic_results = [RetrievalResult(
        chunk=chunk, distance=0.3, source="semantic")]

    monkeypatch.setattr(retriever, "filter_retrieve",
                        lambda ticket, k=5: filter_results)
    monkeypatch.setattr(retriever, "semantic_retrieve",
                        lambda ticket, k=5: semantic_results)

    results = retriever.hybrid_retrieve(good_ticket)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == chunk.chunk_id
    assert results[0].source == "hybrid"
    assert results[0].distance == 0.3
