from __future__ import annotations

import pytest

from src.core.request_models import Ticket
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolInput, RetrievalToolOutput
from src.tools.retriever_tool import RetrieverTool


# ---------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------


@pytest.fixture
def sample_ticket() -> Ticket:
    return Ticket(
        ticket_id="ticket-001",
        turn_id="turn-001",
        source="test",
        description="My iPhone battery drains very quickly after the latest update.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )


def make_decision(
    *,
    use_rag: bool,
    retrieval_mode: str,
    use_memory: bool = False,
    decision_type: str = "metadata_and_description",
    reason: str = "Test decision",
    is_initial_turn: bool = True,
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        retrieval_mode=retrieval_mode,
        decision_type=decision_type,
        reason=reason,
        is_initial_turn=is_initial_turn,
    )


def make_tool_input(
    *,
    ticket: Ticket,
    use_rag: bool,
    retrieval_mode: str,
    query: str | None = None,
    k: int = 5,
    use_memory: bool = False,
    decision_type: str = "metadata_and_description",
    is_initial_turn: bool = True,
) -> RetrievalToolInput:
    return RetrievalToolInput(
        ticket=ticket,
        decision=make_decision(
            use_rag=use_rag,
            use_memory=use_memory,
            retrieval_mode=retrieval_mode,
            decision_type=decision_type,
            is_initial_turn=is_initial_turn,
        ),
        query=query,
        k=k,
    )


class FakeRetriever:
    """
    Fake retriever used to unit test RetrieverTool without embeddings,
    FAISS, vector stores or real KnowledgeChunk objects.
    """

    def __init__(self):
        self.calls: list[dict] = []

    def filter_retrieve(self, ticket, query: str | None = None, k: int | None = None):
        self.calls.append(
            {
                "method": "filter",
                "ticket": ticket,
                "query": query,
                "k": k,
            }
        )
        return []

    def semantic_retrieve(self, ticket, query: str | None = None, k: int = 5):
        self.calls.append(
            {
                "method": "semantic",
                "ticket": ticket,
                "query": query,
                "k": k,
            }
        )
        return []

    def hybrid_retrieve(
        self,
        ticket,
        query: str | None = None,
        k: int = 5,
        semantic_relative_ratio: float = 1.30,
    ):
        self.calls.append(
            {
                "method": "hybrid",
                "ticket": ticket,
                "query": query,
                "k": k,
                "semantic_relative_ratio": semantic_relative_ratio,
            }
        )
        return []


@pytest.fixture
def fake_retriever() -> FakeRetriever:
    return FakeRetriever()


@pytest.fixture
def retriever_tool(fake_retriever: FakeRetriever) -> RetrieverTool:
    return RetrieverTool(retriever=fake_retriever)


# ---------------------------------------------------------------------
# Unit tests: no RAG / none mode consistency
# ---------------------------------------------------------------------


def test_invoke_when_use_rag_false_and_mode_none_returns_empty_output(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=False,
        retrieval_mode="none",
        query=None,
        k=5,
        decision_type="closing",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert isinstance(output, RetrievalToolOutput)

    assert output.called is False
    assert output.mode_used == "none"
    assert output.called is False and output.mode_used == "none"

    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert fake_retriever.calls == []


def test_invoke_when_use_rag_false_and_mode_none_ignores_query(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=False,
        retrieval_mode="none",
        query="optimized query that should not be used",
        k=5,
        decision_type="closing",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is False
    assert output.mode_used == "none"
    assert output.called is False and output.mode_used == "none"

    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert fake_retriever.calls == []


def test_invoke_when_mode_none_returns_consistent_empty_output(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=False,
        retrieval_mode="none",
        query="   ",
        k=3,
        decision_type="closing",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is False
    assert output.mode_used == "none"
    assert output.called is False and output.mode_used == "none"

    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 0


# ---------------------------------------------------------------------
# Unit tests: invalid policy combinations
# ---------------------------------------------------------------------


def test_invoke_raises_when_mode_none_but_use_rag_true(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="none",
        query=None,
        k=5,
        decision_type="metadata_and_description",
        is_initial_turn=True,
    )

    with pytest.raises(ValueError, match="Use Rag must be False"):
        retriever_tool.invoke(tool_input)

    assert fake_retriever.calls == []


@pytest.mark.parametrize("retrieval_mode", ["filter", "semantic", "hybrid"])
def test_invoke_raises_when_mode_requires_rag_but_use_rag_false(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
    retrieval_mode: str,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=False,
        retrieval_mode=retrieval_mode,
        query=None,
        k=5,
        decision_type="metadata_and_description",
        is_initial_turn=True,
    )

    with pytest.raises(ValueError, match="Use Rag must be True"):
        retriever_tool.invoke(tool_input)

    assert fake_retriever.calls == []


# ---------------------------------------------------------------------
# Unit tests: mode dispatch
# ---------------------------------------------------------------------


def test_invoke_filter_mode_calls_filter_retrieve(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="filter",
        query=None,
        k=5,
        decision_type="metadata_only",
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "filter"
    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "filter"
    assert fake_retriever.calls[0]["ticket"] == sample_ticket
    assert fake_retriever.calls[0]["query"] == sample_ticket.description
    assert fake_retriever.calls[0]["k"] == 5


def test_invoke_semantic_mode_calls_semantic_retrieve(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="semantic",
        query=None,
        k=4,
        decision_type="description_only",
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "semantic"
    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "semantic"
    assert fake_retriever.calls[0]["ticket"] == sample_ticket
    assert fake_retriever.calls[0]["query"] == sample_ticket.description
    assert fake_retriever.calls[0]["k"] == 4


def test_invoke_hybrid_mode_calls_hybrid_retrieve(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="hybrid",
        query=None,
        k=6,
        decision_type="metadata_and_description",
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "hybrid"
    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "hybrid"
    assert fake_retriever.calls[0]["ticket"] == sample_ticket
    assert fake_retriever.calls[0]["query"] == sample_ticket.description
    assert fake_retriever.calls[0]["k"] == 6
    assert fake_retriever.calls[0]["semantic_relative_ratio"] == 1.30


# ---------------------------------------------------------------------
# Unit tests: query handling
# ---------------------------------------------------------------------


@pytest.mark.parametrize("empty_query", [None, "", "   ", "\n", "\t"])
def test_invoke_uses_ticket_description_when_query_is_missing_or_empty(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
    empty_query: str | None,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="semantic",
        query=empty_query,
        k=5,
        decision_type="description_only",
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "semantic"
    assert output.optimized_query is None

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "semantic"
    assert fake_retriever.calls[0]["query"] == sample_ticket.description


def test_invoke_uses_optimized_query_when_valid_query_is_provided(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    optimized_query = "iphone battery drain after ios update overheating"

    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="semantic",
        query=optimized_query,
        k=5,
        use_memory=True,
        decision_type="problem_update",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "semantic"
    assert output.optimized_query == optimized_query

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["query"] == optimized_query


def test_invoke_strips_optimized_query_before_using_it(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    raw_query = "   iphone battery drain after update   "
    expected_query = "iphone battery drain after update"

    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="filter",
        query=raw_query,
        k=5,
        decision_type="metadata_only",
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "filter"
    assert output.optimized_query == expected_query

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["query"] == expected_query


def test_invoke_keeps_optimized_query_even_if_equal_to_ticket_description(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode="semantic",
        query=sample_ticket.description,
        k=5,
        use_memory=True,
        decision_type="problem_update",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "semantic"
    assert output.optimized_query == sample_ticket.description

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["query"] == sample_ticket.description


# ---------------------------------------------------------------------
# Unit tests: k handling
# ---------------------------------------------------------------------


@pytest.mark.parametrize("retrieval_mode", ["filter", "semantic", "hybrid"])
def test_invoke_passes_k_from_retrieval_tool_input(
    retriever_tool: RetrieverTool,
    fake_retriever: FakeRetriever,
    sample_ticket: Ticket,
    retrieval_mode: str,
):
    decision_type_by_mode = {
        "filter": "metadata_only",
        "semantic": "description_only",
        "hybrid": "metadata_and_description",
    }

    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode=retrieval_mode,
        query="battery issue",
        k=2,
        decision_type=decision_type_by_mode[retrieval_mode],
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == retrieval_mode

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == retrieval_mode
    assert fake_retriever.calls[0]["k"] == 2


# ---------------------------------------------------------------------
# Unit tests: output consistency
# ---------------------------------------------------------------------


@pytest.mark.parametrize("retrieval_mode", ["filter", "semantic", "hybrid"])
def test_invoke_returns_called_true_for_all_rag_modes(
    retriever_tool: RetrieverTool,
    sample_ticket: Ticket,
    retrieval_mode: str,
):
    decision_type_by_mode = {
        "filter": "metadata_only",
        "semantic": "description_only",
        "hybrid": "metadata_and_description",
    }

    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=True,
        retrieval_mode=retrieval_mode,
        query="battery issue",
        k=5,
        decision_type=decision_type_by_mode[retrieval_mode],
        is_initial_turn=True,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == retrieval_mode
    assert output.optimized_query == "battery issue"
    assert output.results == []
    assert output.total_results == 0


def test_empty_output_contract_is_consistent_for_no_rag(
    retriever_tool: RetrieverTool,
    sample_ticket: Ticket,
):
    tool_input = make_tool_input(
        ticket=sample_ticket,
        use_rag=False,
        retrieval_mode="none",
        query=None,
        k=5,
        decision_type="closing",
        is_initial_turn=False,
    )

    output = retriever_tool.invoke(tool_input)

    assert output.called is False
    assert output.mode_used == "none"
    assert output.called is False and output.mode_used == "none"

    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0


# ---------------------------------------------------------------------
# Lightweight integration-style tests
# ---------------------------------------------------------------------
# These still use FakeRetriever, but test the complete RetrieverToolInput
# -> RetrieverTool.invoke -> RetrievalToolOutput path.
# They are integration-style at the tool boundary, not full RAG integration.
# Full FAISS/embedding integration should stay in tests/test_retriever.py.
# ---------------------------------------------------------------------


def test_tool_boundary_integration_first_turn_hybrid_uses_description(
    sample_ticket: Ticket,
):
    fake_retriever = FakeRetriever()
    tool = RetrieverTool(retriever=fake_retriever)

    decision = RetrievalPolicyDecision(
        use_rag=True,
        use_memory=False,
        retrieval_mode="hybrid",
        decision_type="metadata_and_description",
        reason="Initial turn with rich metadata and description.",
        is_initial_turn=True,
    )

    tool_input = RetrievalToolInput(
        ticket=sample_ticket,
        decision=decision,
        query=None,
        k=5,
    )

    output = tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "hybrid"
    assert output.optimized_query is None
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "hybrid"
    assert fake_retriever.calls[0]["query"] == sample_ticket.description
    assert fake_retriever.calls[0]["k"] == 5


def test_tool_boundary_integration_follow_up_semantic_uses_optimized_query(
    sample_ticket: Ticket,
):
    fake_retriever = FakeRetriever()
    tool = RetrieverTool(retriever=fake_retriever)

    decision = RetrievalPolicyDecision(
        use_rag=True,
        use_memory=True,
        retrieval_mode="semantic",
        decision_type="problem_update",
        reason="Follow-up turn with new problem information.",
        is_initial_turn=False,
    )

    optimized_query = "iphone battery drains after update and device gets warm"

    tool_input = RetrievalToolInput(
        ticket=sample_ticket,
        decision=decision,
        query=optimized_query,
        k=5,
    )

    output = tool.invoke(tool_input)

    assert output.called is True
    assert output.mode_used == "semantic"
    assert output.optimized_query == optimized_query
    assert output.total_results == 0

    assert len(fake_retriever.calls) == 1
    assert fake_retriever.calls[0]["method"] == "semantic"
    assert fake_retriever.calls[0]["query"] == optimized_query
    assert fake_retriever.calls[0]["k"] == 5


def test_tool_boundary_integration_closing_turn_does_not_call_retriever(
    sample_ticket: Ticket,
):
    fake_retriever = FakeRetriever()
    tool = RetrieverTool(retriever=fake_retriever)

    decision = RetrievalPolicyDecision(
        use_rag=False,
        use_memory=False,
        retrieval_mode="none",
        decision_type="closing",
        reason="User is closing the conversation.",
        is_initial_turn=False,
    )

    tool_input = RetrievalToolInput(
        ticket=sample_ticket,
        decision=decision,
        query=None,
        k=5,
    )

    output = tool.invoke(tool_input)

    assert output.called is False
    assert output.mode_used == "none"
    assert output.called is False and output.mode_used == "none"

    assert output.optimized_query is None
    assert output.results == []
    assert output.total_results == 0

    assert fake_retriever.calls == []
