from __future__ import annotations

from src.core.config import (
    GOOGLE_API_KEY,
    DEFAULT_CLOSED_TICKET_RESPONSE,
    DEFAULT_ALREADY_ESCALATED_RESPONSE,
    DEFAULT_FORCE_ESCALATION_RESPONSE,
    DEFAULT_RETRIEVAL_K,
)
from src.core.request_models import Ticket
from src.core.memory_models import MemoryUpdateInput
from src.core.retrieval_policy_models import RetrievalPolicyInput
from src.core.query_rewriter_models import QueryRewriterInput
from src.core.retrieval_tool_models import RetrievalToolInput
from src.core.summary_models import SummaryInput
from src.core.response_models import ResponseInput
from src.core.pipeline_models import PipelineOutput
from src.core.default_models import (
    PredefinedEscalationResponse,
    PredefinedClosingResponse,
)

from src.validation.input_validator import InputValidator
from src.conversation.conversation_state_loader import ConversationStateLoader
from src.conversation.conversation_state_store import InMemoryConversationStateStore
from src.conversation.conversation_updater import ConversationUpdater
from src.memory.memory_store import InMemoryConversationStore
from src.memory.memory_loader import MemoryLoader
from src.rag.retrieval_policy import RetrievalPolicy
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.tools.retriever_tool import RetrieverTool
from src.rag.context_builder import ContextBuilder
from src.agents.summary_agent import SummaryAgent
from src.agents.response_agent import ResponseAgent
from src.agents.memory_agent import MemoryAgent


class SupportPipeline:
    def __init__(
        self,
        input_validator: InputValidator,
        conversation_state_loader: ConversationStateLoader,
        conversation_state_store: InMemoryConversationStateStore,
        conversation_updater: ConversationUpdater,
        memory_store: InMemoryConversationStore,
        memory_loader: MemoryLoader,
        retrieval_policy: RetrievalPolicy,
        query_rewriter_agent: QueryRewriterAgent,
        retriever_tool: RetrieverTool,
        context_builder: ContextBuilder,
        summary_agent: SummaryAgent,
        response_agent: ResponseAgent,
        memory_agent: MemoryAgent,
        max_rag_calls_per_ticket: int,
        max_turns_per_ticket: int
    ) -> None:
        self.input_validator = input_validator
        self.conversation_state_loader = conversation_state_loader
        self.conversation_state_store = conversation_state_store
        self.conversation_updater = conversation_updater
        self.memory_store = memory_store
        self.memory_loader = memory_loader
        self.retrieval_policy = retrieval_policy
        self.query_rewriter_agent = query_rewriter_agent
        self.retriever_tool = retriever_tool
        self.context_builder = context_builder
        self.summary_agent = summary_agent
        self.response_agent = response_agent
        self.memory_agent = memory_agent
        self.max_rag_calls_per_ticket = max_rag_calls_per_ticket
        self.max_turns_per_ticket = max_turns_per_ticket

    def run_turn(self, ticket: Ticket) -> PipelineOutput:
        nodes_executed: list[str] = []

        validated_ticket = self.input_validator.validate(ticket=ticket)
        nodes_executed.append("validate_input_ticket")

        if not validated_ticket.ticket_id:
            raise ValueError("ticket_id is required to run SupportPipeline")

        previous_conversation_state = self.conversation_state_loader.load(
            ticket_id=validated_ticket.ticket_id
        )
        nodes_executed.append("load_conversation_state")

        previous_conversation_memory = None
        memory_after = None
        retrieval_decision = None
        query_rewriter_output = None
        retrieval_output = None
        built_context = None
        summary = None

        # ------------------------------------------------------------------
        # Initial route classification
        # ------------------------------------------------------------------

        if previous_conversation_state.status == "closed":
            initial_route = "already_closed"

        elif previous_conversation_state.status == "escalated":
            initial_route = "already_escalated"

        elif previous_conversation_state.turn_count >= self.max_turns_per_ticket:
            initial_route = "force_escalation"

        elif previous_conversation_state.rag_call_count >= self.max_rag_calls_per_ticket:
            initial_route = "rag_limit_reached"

        else:
            initial_route = "active"

        nodes_executed.append("classify_initial_route")

        # ------------------------------------------------------------------
        # Already closed
        # ------------------------------------------------------------------

        if initial_route == "already_closed":
            response = PredefinedClosingResponse(
                response=DEFAULT_CLOSED_TICKET_RESPONSE
            )
            nodes_executed.append("already_closed_response")

            return PipelineOutput(
                ticket=validated_ticket,
                initial_route=initial_route,
                previous_conversation_state=previous_conversation_state,
                conversation_state_after=previous_conversation_state,
                previous_conversation_memory=None,
                memory_after=None,
                retrieval_decision=None,
                query_rewriter_output=None,
                retrieval_output=None,
                built_context=None,
                summary=None,
                response=response,
                nodes_executed=nodes_executed,
            )

        # ------------------------------------------------------------------
        # Already escalated
        # ------------------------------------------------------------------

        if initial_route == "already_escalated":
            response = PredefinedEscalationResponse(
                response=DEFAULT_ALREADY_ESCALATED_RESPONSE
            )
            nodes_executed.append("already_escalated_response")

            return PipelineOutput(
                ticket=validated_ticket,
                initial_route=initial_route,
                previous_conversation_state=previous_conversation_state,
                conversation_state_after=previous_conversation_state,
                previous_conversation_memory=None,
                memory_after=None,
                retrieval_decision=None,
                query_rewriter_output=None,
                retrieval_output=None,
                built_context=None,
                summary=None,
                response=response,
                nodes_executed=nodes_executed,
            )

        # ------------------------------------------------------------------
        # Force escalation by max turns
        # ------------------------------------------------------------------

        if initial_route == "force_escalation":
            response = PredefinedEscalationResponse(
                response=DEFAULT_FORCE_ESCALATION_RESPONSE
            )
            nodes_executed.append("force_escalation_response")

            conversation_state_after = self.conversation_updater.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                retrieval_decision=None,
                response=None,
                predefined_closing_response=None,
                predefined_escalation_response=response,
            )
            nodes_executed.append("update_conversation")

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=conversation_state_after,
            )
            nodes_executed.append("save_conversation_state")

            return PipelineOutput(
                ticket=validated_ticket,
                initial_route=initial_route,
                previous_conversation_state=previous_conversation_state,
                conversation_state_after=conversation_state_after,
                previous_conversation_memory=None,
                memory_after=None,
                retrieval_decision=None,
                query_rewriter_output=None,
                retrieval_output=None,
                built_context=None,
                summary=None,
                response=response,
                nodes_executed=nodes_executed,
            )

        # ------------------------------------------------------------------
        # Load memory for active/rag-limit branches
        # ------------------------------------------------------------------

        loaded_memory = self.memory_loader.load(
            ticket_id=validated_ticket.ticket_id
        )
        nodes_executed.append("load_memory")

        previous_conversation_memory = loaded_memory.memory
        memory_text = (
            loaded_memory.memory.memory
            if loaded_memory.has_memory and loaded_memory.memory is not None
            else None
        )

        # ------------------------------------------------------------------
        # RAG limit reached
        # ------------------------------------------------------------------

        if initial_route == "rag_limit_reached":
            response = self.response_agent.generate_response(
                response_input=ResponseInput(
                    ticket=validated_ticket,
                    summary=None,
                    memory_context=memory_text,
                )
            )
            nodes_executed.append("generate_response_output")

            memory_after = self.memory_agent.update_memory(
                memory_update_input=MemoryUpdateInput(
                    ticket=validated_ticket,
                    previous_memory=previous_conversation_memory,
                    summary=None,
                    response=response,
                )
            )
            nodes_executed.append("generate_new_memory")

            self.memory_store.save(
                ticket_id=validated_ticket.ticket_id,
                memory=memory_after,
            )
            nodes_executed.append("save_conversation_memory")

            conversation_state_after = self.conversation_updater.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                retrieval_decision=None,
                response=response,
                predefined_closing_response=None,
                predefined_escalation_response=None,
            )
            nodes_executed.append("update_conversation")

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=conversation_state_after,
            )
            nodes_executed.append("save_conversation_state")

            return PipelineOutput(
                ticket=validated_ticket,
                initial_route=initial_route,
                previous_conversation_state=previous_conversation_state,
                conversation_state_after=conversation_state_after,
                previous_conversation_memory=previous_conversation_memory,
                memory_after=memory_after,
                retrieval_decision=None,
                query_rewriter_output=None,
                retrieval_output=None,
                built_context=None,
                summary=None,
                response=response,
                nodes_executed=nodes_executed,
            )

        # ------------------------------------------------------------------
        # Active normal flow
        # ------------------------------------------------------------------

        retrieval_decision = self.retrieval_policy.decide(
            policy_input=RetrievalPolicyInput(
                ticket=validated_ticket,
                memory_context=memory_text,
            )
        )
        nodes_executed.append("retrieval_policy_decision")

        if retrieval_decision.use_rag:
            should_rewrite_query = (
                not retrieval_decision.is_initial_turn
                and retrieval_decision.use_memory
                and loaded_memory.has_memory
                and loaded_memory.memory is not None
            )

            if should_rewrite_query:
                query_rewriter_output = self.query_rewriter_agent.rewrite(
                    query_rewriter_input=QueryRewriterInput(
                        current_description=validated_ticket.description,
                        memory_context=memory_text,
                    )
                )
                nodes_executed.append("rewrite_query")

            query = (
                query_rewriter_output.optimized_query
                if query_rewriter_output is not None
                else None
            )

            retrieval_output = self.retriever_tool.invoke(
                retrieval_tool_input=RetrievalToolInput(
                    ticket=validated_ticket,
                    decision=retrieval_decision,
                    query=query,
                    k=DEFAULT_RETRIEVAL_K,
                )
            )
            nodes_executed.append("retrieve_results_tool")

            if retrieval_output.results:
                built_context = self.context_builder.build(
                    retrieval_results=retrieval_output.results
                )
                nodes_executed.append("build_context")

                summary = self.summary_agent.summarize(
                    summary_input=SummaryInput(
                        ticket=validated_ticket,
                        built_context=built_context,
                        memory_context=memory_text,
                    )
                )
                nodes_executed.append("build_summary")

        response = self.response_agent.generate_response(
            response_input=ResponseInput(
                ticket=validated_ticket,
                summary=summary,
                memory_context=memory_text,
            )
        )
        nodes_executed.append("generate_response_output")

        memory_after = self.memory_agent.update_memory(
            memory_update_input=MemoryUpdateInput(
                ticket=validated_ticket,
                previous_memory=previous_conversation_memory,
                summary=summary,
                response=response,
            )
        )
        nodes_executed.append("generate_new_memory")

        self.memory_store.save(
            ticket_id=validated_ticket.ticket_id,
            memory=memory_after,
        )
        nodes_executed.append("save_conversation_memory")

        conversation_state_after = self.conversation_updater.update_state(
            previous_state=previous_conversation_state,
            ticket=validated_ticket,
            retrieval_decision=retrieval_decision,
            response=response,
            predefined_closing_response=None,
            predefined_escalation_response=None,
        )
        nodes_executed.append("update_conversation")

        self.conversation_state_store.save(
            ticket_id=validated_ticket.ticket_id,
            state=conversation_state_after,
        )
        nodes_executed.append("save_conversation_state")

        return PipelineOutput(
            ticket=validated_ticket,
            initial_route=initial_route,
            previous_conversation_state=previous_conversation_state,
            conversation_state_after=conversation_state_after,
            previous_conversation_memory=previous_conversation_memory,
            memory_after=memory_after,
            retrieval_decision=retrieval_decision,
            query_rewriter_output=query_rewriter_output,
            retrieval_output=retrieval_output,
            built_context=built_context,
            summary=summary,
            response=response,
            nodes_executed=nodes_executed,
        )
