from __future__ import annotations

from typing import Literal

from src.core.response_models import ResponseOutput
from src.graph.graph_state import SupportGraphState


InitialRoute = Literal[
    "already_closed",
    "already_escalated",
    "force_escalation",
    "rag_limit_reached",
    "active"]

AfterMemoryRoute = Literal[
    "retrieval_policy",
    "response_agent_no_rag"]

AfterRetrievalPolicyRoute = Literal[
    "response_agent_no_rag",
    "query_rewriter_agent",
    "retriever_tool"]


AfterRetrievalRoute = Literal[
    "build_context",
    "response_agent_without_summary"]


def route_initial_state(state: SupportGraphState) -> InitialRoute:
    initial_route = state.get("initial_route")

    if initial_route is None:
        raise ValueError("an initial route is required to decide next conditional node in initial routing.")

    valid_routes = {
        "already_closed",
        "already_escalated",
        "force_escalation",
        "rag_limit_reached",
        "active",
    }

    if initial_route not in valid_routes:
        raise ValueError(f"invalid initial route: {initial_route}")

    return initial_route


def route_after_memory(state: SupportGraphState) -> AfterMemoryRoute:
    initial_route = state.get("initial_route")
    loaded_memory = state.get("previous_conversation_memory")

    if initial_route is None:
        raise ValueError("initial_route is required to decide next conditional node after memory loading.")

    if loaded_memory is None:
        raise ValueError("previous_conversation_memory is required after memory loading.")

    if initial_route == "rag_limit_reached":
        return "response_agent_no_rag"

    if initial_route == "active":
        return "retrieval_policy"

    raise ValueError(f"invalid initial_route after memory loading: {initial_route}")


def route_after_retrieval_policy(state: SupportGraphState) -> AfterRetrievalPolicyRoute:
    retrieval_policy_decision = state.get("retrieval_decision")
    loaded_memory = state.get("previous_conversation_memory")

    if retrieval_policy_decision is None:
        raise ValueError("retrieval_decision is required to decide next conditional node in retrieval-policy routing.")

    if loaded_memory is None:
        raise ValueError(
            "previous_conversation_memory is required to decide next conditional node in retrieval-policy routing.")

    if retrieval_policy_decision.use_rag is False:
        return "response_agent_no_rag"

    if (
        retrieval_policy_decision.is_initial_turn is False
        and retrieval_policy_decision.use_memory is True
        and loaded_memory.has_memory is True
    ):
        return "query_rewriter_agent"

    return "retriever_tool"


def route_after_retrieval(state: SupportGraphState) -> AfterRetrievalRoute:
    retrieval_output = state.get("retrieval_output")

    if retrieval_output is None:
        raise ValueError("retrieval_output is required to decide next conditional node after retrieval.")

    if retrieval_output.total_results > 0:
        return "build_context"

    return "response_agent_without_summary"
