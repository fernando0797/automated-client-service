from src.rag.context_builder import ContextBuilder
from src.core.models import RetrievalResult, KnowledgeChunk


def make_result(
    chunk_type: str,
    content: str,
    chunk_id: str = "chunk-1",
    parent_doc_id: str = "doc-1",
    distance: float = 0.1,
    source: str = "test-source",
) -> RetrievalResult:
    chunk = KnowledgeChunk(
        chunk_id=chunk_id,
        parent_doc_id=parent_doc_id,
        content=content,
        metadata={"type": chunk_type},
    )

    return RetrievalResult(
        chunk=chunk,
        distance=distance,
        source=source,
    )


def test_build_creates_context_with_sections_in_expected_order():
    builder = ContextBuilder()
    retrieval_results = [
        make_result("domain", "domain text 1", chunk_id="d1"),
        make_result("product", "product text 1", chunk_id="p1"),
        make_result("cross_doc", "cross doc text 1", chunk_id="c1"),
        make_result("subdomain", "subdomain text 1", chunk_id="s1"),
    ]

    built = builder.build(retrieval_results)

    expected_text = (
        "RETRIEVED CONTEXT"
        "\n\nCROSS_DOC\ncross doc text 1"
        "\n\nPRODUCT\nproduct text 1"
        "\n\nSUBDOMAIN\nsubdomain text 1"
        "\n\nDOMAIN\ndomain text 1"
    )

    assert built.context_text == expected_text
    assert built.total_chars == len(expected_text)
    assert built.results_used == retrieval_results


def test_build_omits_empty_sections():
    builder = ContextBuilder()
    retrieval_results = [
        make_result("product", "product text 1", chunk_id="p1"),
        make_result("domain", "domain text 1", chunk_id="d1"),
    ]

    built = builder.build(retrieval_results)

    assert "CROSS_DOC" not in built.context_text
    assert "SUBDOMAIN" not in built.context_text
    assert "PRODUCT" in built.context_text
    assert "DOMAIN" in built.context_text


def test_build_with_empty_results_returns_header_only():
    builder = ContextBuilder()

    built = builder.build([])

    assert built.context_text == "RETRIEVED CONTEXT"
    assert built.total_chars == len("RETRIEVED CONTEXT")
    assert built.results_used == []


def test_build_preserves_order_within_each_section():
    builder = ContextBuilder()
    retrieval_results = [
        make_result("product", "product text 1", chunk_id="p1"),
        make_result("domain", "domain text 1", chunk_id="d1"),
        make_result("product", "product text 2", chunk_id="p2"),
        make_result("domain", "domain text 2", chunk_id="d2"),
    ]

    built = builder.build(retrieval_results)

    product_block = "PRODUCT\nproduct text 1\n\nproduct text 2"
    domain_block = "DOMAIN\ndomain text 1\n\ndomain text 2"

    assert product_block in built.context_text
    assert domain_block in built.context_text


def test_build_groups_same_type_together_even_if_input_is_mixed():
    builder = ContextBuilder()
    retrieval_results = [
        make_result("domain", "domain text", chunk_id="d1"),
        make_result("cross_doc", "cross doc text", chunk_id="c1"),
        make_result("product", "product text", chunk_id="p1"),
        make_result("subdomain", "subdomain text", chunk_id="s1"),
        make_result("cross_doc", "cross doc text 2", chunk_id="c2"),
    ]

    built = builder.build(retrieval_results)

    expected_text = (
        "RETRIEVED CONTEXT"
        "\n\nCROSS_DOC\ncross doc text\n\ncross doc text 2"
        "\n\nPRODUCT\nproduct text"
        "\n\nSUBDOMAIN\nsubdomain text"
        "\n\nDOMAIN\ndomain text"
    )

    assert built.context_text == expected_text


def test_total_chars_matches_context_text_length():
    builder = ContextBuilder()
    retrieval_results = [
        make_result("cross_doc", "abc", chunk_id="c1"),
        make_result("product", "xyz", chunk_id="p1"),
    ]

    built = builder.build(retrieval_results)

    assert built.total_chars == len(built.context_text)
