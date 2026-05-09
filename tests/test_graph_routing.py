from __future__ import annotations

import pytest

from src.core.memory_models import ConversationMemory, LoadedMemory
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.graph.routing import (
    route_after_memory,
    route_after_retrieval,
    route_after_retrieval_policy,
    route_initial_state,
)


def loaded_memory_with_content() -> LoadedMemory:
    return LoadedMemory(
        has_memory=True,
        memory=ConversationMemory(memory="User reported an overheating issue."),
    )


def loaded_memory_empty() -> LoadedMemory:
    return LoadedMemory(
        has_memory=False,
        memory=None,
    )


def retrieval_decision(
    *,
    use_rag: bool,
    use_memory: bool,
    is_initial_turn: bool,
    retrieval_mode: str = "none",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type="metadata_and_description",
        reason="test decision",
    )


def retrieval_output_with_total(total_results: int) -> RetrievalToolOutput:
    return RetrievalToolOutput(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[],
        total_results=total_results,
    )

# ---------------------------------------------------------------------
# route_initial_state
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "initial_route",
    [
        "already_closed",
        "already_escalated",
        "force_escalation",
        "rag_limit_reached",
        "active",
    ],
)
def test_route_initial_state_returns_valid_initial_route(initial_route):
    state = {
        "initial_route": initial_route,
    }

    result = route_initial_state(state)

    assert result == initial_route


def test_route_initial_state_raises_when_initial_route_is_missing():
    state = {}

    with pytest.raises(ValueError, match="initial route is required"):
        route_initial_state(state)


def test_route_initial_state_raises_when_initial_route_is_invalid():
    state = {
        "initial_route": "invalid_route",
    }

    with pytest.raises(ValueError, match="invalid initial route"):
        route_initial_state(state)


# ---------------------------------------------------------------------
# route_after_memory
# ---------------------------------------------------------------------


def test_route_after_memory_goes_to_response_agent_when_rag_limit_reached():
    state = {
        "initial_route": "rag_limit_reached",
        "previous_conversation_memory": loaded_memory_empty(),
    }

    result = route_after_memory(state)

    assert result == "response_agent_no_rag"


def test_route_after_memory_goes_to_retrieval_policy_when_active():
    state = {
        "initial_route": "active",
        "previous_conversation_memory": loaded_memory_empty(),
    }

    result = route_after_memory(state)

    assert result == "retrieval_policy"


def test_route_after_memory_raises_when_initial_route_is_missing():
    state = {
        "previous_conversation_memory": loaded_memory_empty(),
    }

    with pytest.raises(ValueError, match="initial_route is required"):
        route_after_memory(state)


def test_route_after_memory_raises_when_loaded_memory_is_missing():
    state = {
        "initial_route": "active",
    }

    with pytest.raises(ValueError, match="previous_conversation_memory is required"):
        route_after_memory(state)


@pytest.mark.parametrize(
    "invalid_initial_route",
    [
        "already_closed",
        "already_escalated",
        "force_escalation",
        "invalid_route",
    ],
)
def test_route_after_memory_raises_for_invalid_initial_route_after_memory(
    invalid_initial_route,
):
    state = {
        "initial_route": invalid_initial_route,
        "previous_conversation_memory": loaded_memory_empty(),
    }

    with pytest.raises(ValueError, match="invalid initial_route after memory loading"):
        route_after_memory(state)


# ---------------------------------------------------------------------
# route_after_retrieval_policy
# ---------------------------------------------------------------------


def test_route_after_retrieval_policy_goes_to_response_agent_when_use_rag_false():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=False,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="none",
        ),
        "previous_conversation_memory": loaded_memory_with_content(),
    }

    result = route_after_retrieval_policy(state)

    assert result == "response_agent_no_rag"


def test_route_after_retrieval_policy_goes_to_query_rewriter_for_followup_with_memory():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
        ),
        "previous_conversation_memory": loaded_memory_with_content(),
    }

    result = route_after_retrieval_policy(state)

    assert result == "query_rewriter_agent"


def test_route_after_retrieval_policy_goes_to_retriever_for_initial_turn_with_rag():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="hybrid",
        ),
        "previous_conversation_memory": loaded_memory_empty(),
    }

    result = route_after_retrieval_policy(state)

    assert result == "retriever_tool"


def test_route_after_retrieval_policy_goes_to_retriever_for_followup_without_memory():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
        ),
        "previous_conversation_memory": loaded_memory_empty(),
    }

    result = route_after_retrieval_policy(state)

    assert result == "retriever_tool"


def test_route_after_retrieval_policy_goes_to_retriever_when_use_memory_false_even_if_memory_exists():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=False,
            retrieval_mode="semantic",
        ),
        "previous_conversation_memory": loaded_memory_with_content(),
    }

    result = route_after_retrieval_policy(state)

    assert result == "retriever_tool"


def test_route_after_retrieval_policy_raises_when_decision_is_missing():
    state = {
        "previous_conversation_memory": loaded_memory_empty(),
    }

    with pytest.raises(ValueError, match="retrieval_decision is required"):
        route_after_retrieval_policy(state)


def test_route_after_retrieval_policy_raises_when_loaded_memory_is_missing():
    state = {
        "retrieval_decision": retrieval_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
        ),
    }

    with pytest.raises(ValueError, match="previous_conversation_memory is required"):
        route_after_retrieval_policy(state)


# ---------------------------------------------------------------------
# route_after_retrieval
# ---------------------------------------------------------------------


def test_route_after_retrieval_goes_to_build_context_when_results_exist():
    state = {
        "retrieval_output": retrieval_output_with_total(total_results=3),
    }

    result = route_after_retrieval(state)

    assert result == "build_context"


def test_route_after_retrieval_goes_to_response_without_summary_when_no_results():
    state = {
        "retrieval_output": retrieval_output_with_total(total_results=0),
    }

    result = route_after_retrieval(state)

    assert result == "response_agent_without_summary"


def test_route_after_retrieval_raises_when_retrieval_output_is_missing():
    state = {}

    with pytest.raises(ValueError, match="retrieval_output is required"):
        route_after_retrieval(state)
