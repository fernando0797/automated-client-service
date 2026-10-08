from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.graph.graph_state import SupportGraphState
from src.graph.nodes import (
    already_closed_response_node,
    already_escalated_response_node,
    force_escalation_response_node,
    make_build_context_node,
    make_build_summary_node,
    make_classify_initial_route_node,
    make_generate_new_memory_node,
    make_generate_response_output_node,
    make_load_conversation_state_node,
    make_load_memory_node,
    make_retrieval_policy_decision_node,
    make_retrieve_results_tool,
    make_rewrite_query_node,
    make_save_conversation_memory_node,
    make_save_conversation_state_node,
    make_update_conversation_node,
    make_validate_input_ticket_node,
)
from src.graph.routing import (
    route_after_memory,
    route_after_retrieval,
    route_after_retrieval_policy,
    route_initial_state,
)

from src.validation.input_validator import InputValidator
from src.conversation.conversation_state_loader import ConversationStateLoader
from src.conversation.conversation_state_store import InMemoryConversationStateStore
from src.conversation.conversation_updater import ConversationUpdater
from src.memory.memory_loader import MemoryLoader
from src.memory.memory_store import InMemoryConversationStore
from src.rag.retrieval_policy import RetrievalPolicy
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.tools.retriever_tool import RetrieverTool
from src.rag.context_builder import ContextBuilder
from src.agents.summary_agent import SummaryAgent
from src.agents.response_agent import ResponseAgent
from src.agents.memory_agent import MemoryAgent


def build_support_graph(
    *,
    input_validator: InputValidator,
    conversation_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_updater: ConversationUpdater,
    memory_loader: MemoryLoader,
    memory_store: InMemoryConversationStore,
    retrieval_policy: RetrievalPolicy,
    query_rewriter_agent: QueryRewriterAgent,
    retriever_tool: RetrieverTool,
    context_builder: ContextBuilder,
    summary_agent: SummaryAgent,
    response_agent: ResponseAgent,
    memory_agent: MemoryAgent,
    max_turns_per_ticket: int,
    max_rag_calls_per_ticket: int,
):
    graph = StateGraph(SupportGraphState)

    graph.add_node(
        "validate_input_ticket",
        make_validate_input_ticket_node(input_validator),
    )

    graph.add_node(
        "load_conversation_state",
        make_load_conversation_state_node(conversation_loader),
    )

    graph.add_node(
        "classify_initial_route",
        make_classify_initial_route_node(
            max_turns_per_ticket=max_turns_per_ticket,
            max_rag_calls_per_ticket=max_rag_calls_per_ticket,
        ),
    )

    graph.add_node(
        "already_closed_response",
        already_closed_response_node,
    )

    graph.add_node(
        "already_escalated_response",
        already_escalated_response_node,
    )

    graph.add_node(
        "force_escalation_response",
        force_escalation_response_node,
    )

    graph.add_node(
        "load_memory",
        make_load_memory_node(memory_loader),
    )

    graph.add_node(
        "retrieval_policy",
        make_retrieval_policy_decision_node(retrieval_policy),
    )

    graph.add_node(
        "query_rewriter",
        make_rewrite_query_node(query_rewriter_agent),
    )

    graph.add_node(
        "retriever_tool",
        make_retrieve_results_tool(retriever_tool),
    )

    graph.add_node(
        "build_context",
        make_build_context_node(context_builder),
    )

    graph.add_node(
        "build_summary",
        make_build_summary_node(summary_agent),
    )

    graph.add_node(
        "generate_response",
        make_generate_response_output_node(response_agent),
    )

    graph.add_node(
        "generate_new_memory",
        make_generate_new_memory_node(memory_agent),
    )

    graph.add_node(
        "save_conversation_memory",
        make_save_conversation_memory_node(memory_store),
    )

    graph.add_node(
        "update_conversation",
        make_update_conversation_node(conversation_updater),
    )

    graph.add_node(
        "save_conversation_state",
        make_save_conversation_state_node(conversation_state_store),
    )

    graph.add_edge(START, "validate_input_ticket")
    graph.add_edge("validate_input_ticket", "load_conversation_state")
    graph.add_edge("load_conversation_state", "classify_initial_route")

    graph.add_conditional_edges(
        "classify_initial_route",
        route_initial_state,
        {
            "already_closed": "already_closed_response",
            "already_escalated": "already_escalated_response",
            "force_escalation": "force_escalation_response",
            "rag_limit_reached": "load_memory",
            "active": "load_memory",
        },
    )

    graph.add_edge("already_closed_response", END)
    graph.add_edge("already_escalated_response", END)

    graph.add_edge("force_escalation_response", "update_conversation")
    graph.add_edge("update_conversation", "save_conversation_state")
    graph.add_edge("save_conversation_state", END)

    graph.add_conditional_edges(
        "load_memory",
        route_after_memory,
        {
            "response_agent_no_rag": "generate_response",
            "retrieval_policy": "retrieval_policy",
        },
    )

    graph.add_conditional_edges(
        "retrieval_policy",
        route_after_retrieval_policy,
        {
            "response_agent_no_rag": "generate_response",
            "query_rewriter_agent": "query_rewriter",
            "retriever_tool": "retriever_tool",
        },
    )

    graph.add_edge("query_rewriter", "retriever_tool")

    graph.add_conditional_edges(
        "retriever_tool",
        route_after_retrieval,
        {
            "build_context": "build_context",
            "response_agent_without_summary": "generate_response",
        },
    )

    graph.add_edge("build_context", "build_summary")
    graph.add_edge("build_summary", "generate_response")

    graph.add_edge("generate_response", "generate_new_memory")
    graph.add_edge("generate_new_memory", "save_conversation_memory")
    graph.add_edge("save_conversation_memory", "update_conversation")

    return graph.compile()
