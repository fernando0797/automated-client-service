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


# _build_query TESTS

def test_build_query_uses_ticket_description_when_query_is_none(retriever, good_ticket):
    query = retriever._build_query(good_ticket, None)
    assert query == good_ticket.description


def test_build_query_uses_ticket_description_when_query_is_blank(retriever, good_ticket):
    query = retriever._build_query(good_ticket, "   ")
    assert query == good_ticket.description


def test_build_query_uses_external_query_when_provided(retriever, good_ticket):
    optimized_query = "optimized amazon echo setup query"
    query = retriever._build_query(good_ticket, optimized_query)
    assert query == optimized_query


def test_build_query_strips_external_query(retriever, good_ticket):
    optimized_query = "   optimized amazon echo setup query   "
    query = retriever._build_query(good_ticket, optimized_query)
    assert query == "optimized amazon echo setup query"


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
    results = retriever.filter_retrieve(good_ticket, k=None)
    results2 = retriever._filter_chunks(good_ticket)
    assert len(results) == len(results2)


def test_returns_all_filtered_chunks_when_k_is_too_big(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket, k=9999)
    results2 = retriever._filter_chunks(good_ticket)
    assert len(results) == len(results2)


def test_function_doesnt_break_with_negative_k(retriever, good_ticket):
    results = retriever.filter_retrieve(good_ticket, k=-5)
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


def test_filter_retrieve_accepts_external_query(retriever, good_ticket):
    results = retriever.filter_retrieve(
        ticket=good_ticket,
        query="amazon echo setup wizard failure",
        k=3,
    )
    assert isinstance(results, list)
    assert len(results) <= 3
    for result in results:
        assert isinstance(result, RetrievalResult)
        assert result.source == "filter"


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
    results = retriever.semantic_retrieve(good_ticket, k=3)
    assert len(results) <= 3


def test_semantic_retrieve_list_able_to_cut_when_k_too_large(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, k=9999999)
    assert len(results) < 9999999
    assert len(results) == len(retriever.chunks)


def test_semantic_retrieve_list_doesnt_break_with_nonpositive_k_and_defaults_to_5(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, k=-5)
    assert len(results) <= 5


def test_semantic_retrieve_list_ordered_by_distance(retriever, good_ticket):
    results = retriever.semantic_retrieve(good_ticket, k=15)
    distance_list = []
    for result in results:
        distance_list.append(result.distance)
    assert distance_list == sorted(distance_list)


def test_semantic_retrieve_accepts_external_query(retriever, good_ticket):
    results = retriever.semantic_retrieve(
        ticket=good_ticket,
        query="amazon echo setup wizard failure",
        k=3,
    )
    assert isinstance(results, list)
    assert len(results) <= 3
    for result in results:
        assert isinstance(result, RetrievalResult)
        assert result.source == "semantic"


# hybrid_retrieve TESTS

def test_hybrid_retrieve_returns_list(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    assert isinstance(results, list)


def test_hybrid_retrieve_list_contains_RetrievalResult(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    for result in results:
        assert isinstance(result, RetrievalResult)


def test_hybrid_retrieve_list_length_never_larger_than_k(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket, k=3)
    assert len(results) <= 3


def test_hybrid_retrieve_list_doesnt_break_with_nonpositive_k_and_defaults_to_5(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket, k=-4)
    assert len(results) <= 5


def test_hybrid_retrieve_guaranteed_filter_block_is_sorted_by_distance(retriever, good_ticket):
    k = 5
    results = retriever.hybrid_retrieve(good_ticket, k=k)

    guaranteed_filter_k = k - min(2, max(k - 1, 0))
    guaranteed_block = results[:guaranteed_filter_k]

    distance_list = []
    for result in guaranteed_block:
        distance_list.append(result.distance)

    assert distance_list == sorted(distance_list)


def test_hybrid_retrieve_remaining_block_is_sorted_by_distance(retriever, good_ticket):
    k = 5
    results = retriever.hybrid_retrieve(good_ticket, k=k)

    guaranteed_filter_k = k - min(2, max(k - 1, 0))
    remaining_block = results[guaranteed_filter_k:]

    distance_list = []
    for result in remaining_block:
        distance_list.append(result.distance)

    assert distance_list == sorted(distance_list)


def test_hybrid_retrieve_list_has_no_duplicates(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    chunkids = []
    for result in results:
        chunkids.append(result.chunk.chunk_id)
    assert len(chunkids) == len(set(chunkids))


def test_hybrid_retrieve_contains_valid_source(retriever, good_ticket):
    results = retriever.hybrid_retrieve(good_ticket)
    for result in results:
        assert result.source in {"semantic", "filter"}


def test_hybrid_retrieve_accepts_external_query(retriever, good_ticket):
    results = retriever.hybrid_retrieve(
        ticket=good_ticket,
        query="amazon echo setup wizard failure",
        k=5,
    )
    assert isinstance(results, list)
    assert len(results) <= 5
    for result in results:
        assert isinstance(result, RetrievalResult)


def test_hybrid_retrieve_returns_semantic_when_no_filter_results(monkeypatch, retriever, good_ticket):
    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.1, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.2, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.3, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: [],
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=2)

    assert results == semantic_results[:2]
    assert len(results) == 2
    for result in results:
        assert result.source == "semantic"


def test_hybrid_retrieve_guarantees_k_minus_two_filter_results_when_possible(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.10, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.20, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.30, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[3], distance=0.90, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[4], distance=1.00, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[5], distance=0.40, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[6], distance=0.50, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=5)

    assert len(results) == 5

    guaranteed_filter_results = results[:3]
    for result in guaranteed_filter_results:
        assert result.source == "filter"

    assert len([result for result in results if result.source == "filter"]) >= 3


def test_hybrid_retrieve_reserves_last_two_slots_for_best_remaining_candidates(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.10, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.20, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.30, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[3], distance=0.80, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[4], distance=0.90, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[5], distance=0.40, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[6], distance=0.50, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=5)

    result_ids = [result.chunk.chunk_id for result in results]

    assert retriever.chunks[0].chunk_id in result_ids
    assert retriever.chunks[1].chunk_id in result_ids
    assert retriever.chunks[2].chunk_id in result_ids
    assert retriever.chunks[5].chunk_id in result_ids
    assert retriever.chunks[6].chunk_id in result_ids

    assert retriever.chunks[3].chunk_id not in result_ids
    assert retriever.chunks[4].chunk_id not in result_ids


def test_hybrid_retrieve_removes_semantic_candidates_already_present_in_filter(monkeypatch, retriever, good_ticket):
    duplicated_chunk = retriever.chunks[3]

    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.10, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.20, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.30, source="filter"),
        RetrievalResult(chunk=duplicated_chunk,
                        distance=0.80, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(chunk=duplicated_chunk,
                        distance=0.05, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[4], distance=0.40, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=5)
    duplicated_results = [
        result for result in results
        if result.chunk.chunk_id == duplicated_chunk.chunk_id
    ]

    assert len(duplicated_results) == 1
    assert duplicated_results[0].source == "filter"


def test_hybrid_retrieve_filters_out_semantic_candidates_that_are_too_far(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.10, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.20, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.30, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[3], distance=0.50, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[4], distance=0.60, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[5], distance=10.00, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[6], distance=11.00, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(
        good_ticket, k=5, semantic_relative_ratio=1.30)

    result_ids = [result.chunk.chunk_id for result in results]

    assert retriever.chunks[5].chunk_id not in result_ids
    assert retriever.chunks[6].chunk_id not in result_ids
    assert len(results) == 5
    for result in results:
        assert result.source == "filter"


def test_hybrid_retrieve_uses_selected_filter_results_as_threshold_reference_when_no_filter_candidate_pool(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.10, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.20, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.25, source="semantic"),
        RetrievalResult(
            chunk=retriever.chunks[3], distance=10.00, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(
        good_ticket, k=5, semantic_relative_ratio=1.30)
    result_ids = [result.chunk.chunk_id for result in results]

    assert retriever.chunks[0].chunk_id in result_ids
    assert retriever.chunks[1].chunk_id in result_ids
    assert retriever.chunks[2].chunk_id in result_ids
    assert retriever.chunks[3].chunk_id not in result_ids


def test_hybrid_retrieve_guarantees_one_filter_result_when_k_is_one(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.90, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[1], distance=0.10, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=1)

    assert len(results) == 1
    assert results[0].source == "filter"
    assert results[0].chunk.chunk_id == retriever.chunks[0].chunk_id


def test_hybrid_retrieve_guarantees_one_filter_result_when_k_is_two(monkeypatch, retriever, good_ticket):
    filter_results = [
        RetrievalResult(
            chunk=retriever.chunks[0], distance=0.90, source="filter"),
        RetrievalResult(
            chunk=retriever.chunks[1], distance=1.00, source="filter"),
    ]

    semantic_results = [
        RetrievalResult(
            chunk=retriever.chunks[2], distance=0.10, source="semantic"),
    ]

    monkeypatch.setattr(
        retriever,
        "filter_retrieve",
        lambda ticket, query=None, k=None: filter_results,
    )
    monkeypatch.setattr(
        retriever,
        "semantic_retrieve",
        lambda ticket, query=None, k=5: semantic_results,
    )

    results = retriever.hybrid_retrieve(good_ticket, k=2)

    assert len(results) == 2
    assert results[0].source == "filter"
    assert results[0].chunk.chunk_id == retriever.chunks[0].chunk_id
    assert retriever.chunks[2].chunk_id in [
        result.chunk.chunk_id for result in results]
