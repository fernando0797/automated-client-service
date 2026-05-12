from __future__ import annotations

from typing import Any

from src.core.request_models import Ticket
from src.core.pipeline_models import PipelineOutput
from src.graph.graph_state import SupportGraphState
from src.graph.support_graph import build_support_graph

from src.validation.input_validator import InputValidator
from src.conversation.conversation_updater import ConversationUpdater
from src.rag.retrieval_policy import RetrievalPolicy
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.tools.retriever_tool import RetrieverTool
from src.rag.context_builder import ContextBuilder
from src.agents.summary_agent import SummaryAgent
from src.agents.response_agent import ResponseAgent
from src.agents.memory_agent import MemoryAgent

from src.persistence.repositories.conversation_state_repository import (
    SQLConversationStateStore,
)
from src.persistence.repositories.conversation_memory_repository import (
    SQLConversationMemoryStore,
)
from src.persistence.repositories.turn_trace_repository import SQLTraceStore


class SupportGraphRunner:
    """
    Public runner for the LangGraph-based support pipeline.

    It keeps the external contract as PipelineOutput, while LangGraph handles
    the internal orchestration.
    """

    def __init__(
        self,
        *,
        input_validator: InputValidator,
        conversation_state_store: SQLConversationStateStore,
        conversation_updater: ConversationUpdater,
        memory_store: SQLConversationMemoryStore,
        retrieval_policy: RetrievalPolicy,
        query_rewriter_agent: QueryRewriterAgent,
        retriever_tool: RetrieverTool,
        context_builder: ContextBuilder,
        summary_agent: SummaryAgent,
        response_agent: ResponseAgent,
        memory_agent: MemoryAgent,
        max_turns_per_ticket: int,
        max_rag_calls_per_ticket: int,
        trace_store: SQLTraceStore | None = None,
    ) -> None:
        self.trace_store = trace_store

        self.graph = build_support_graph(
            input_validator=input_validator,
            conversation_loader=conversation_state_store,
            conversation_state_store=conversation_state_store,
            conversation_updater=conversation_updater,
            memory_loader=memory_store,
            memory_store=memory_store,
            retrieval_policy=retrieval_policy,
            query_rewriter_agent=query_rewriter_agent,
            retriever_tool=retriever_tool,
            context_builder=context_builder,
            summary_agent=summary_agent,
            response_agent=response_agent,
            memory_agent=memory_agent,
            max_turns_per_ticket=max_turns_per_ticket,
            max_rag_calls_per_ticket=max_rag_calls_per_ticket,
        )

    def run(self, ticket: Ticket) -> PipelineOutput:
        final_state = self.graph.invoke(
            {
                "ticket": ticket,
                "nodes_executed": [],
            }
        )

        pipeline_output = self._build_pipeline_output(final_state)

        if self.trace_store is not None:
            self.trace_store.save(pipeline_output)

        return pipeline_output

    def _build_pipeline_output(
        self,
        state: SupportGraphState | dict[str, Any],
    ) -> PipelineOutput:
        ticket = state.get("ticket")
        initial_route = state.get("initial_route")
        previous_conversation_state = state.get("previous_conversation_state")
        conversation_state_after = state.get("conversation_state_after")
        response = state.get("response")

        if ticket is None:
            raise ValueError("ticket is required to build PipelineOutput")

        if initial_route is None:
            raise ValueError("initial_route is required to build PipelineOutput")

        if previous_conversation_state is None:
            raise ValueError(
                "previous_conversation_state is required to build PipelineOutput"
            )

        if response is None:
            raise ValueError("response is required to build PipelineOutput")

        if conversation_state_after is None:
            conversation_state_after = previous_conversation_state

        loaded_memory = state.get("previous_conversation_memory")

        previous_conversation_memory = (
            loaded_memory.memory if loaded_memory is not None else None
        )

        return PipelineOutput(
            ticket=ticket,
            initial_route=initial_route,
            previous_conversation_state=previous_conversation_state,
            conversation_state_after=conversation_state_after,
            previous_conversation_memory=previous_conversation_memory,
            memory_after=state.get("memory_after"),
            retrieval_decision=state.get("retrieval_decision"),
            query_rewriter_output=state.get("query_rewriter_output"),
            retrieval_output=state.get("retrieval_output"),
            built_context=state.get("built_context"),
            summary=state.get("summary"),
            response=response,
            nodes_executed=state.get("nodes_executed", []),
        )
