from __future__ import annotations

from src.core.config import (
    GOOGLE_API_KEY,
    DEFAULT_CLOSED_TICKET_RESPONSE,
    DEFAULT_ESCALATION_RESPONSE,
    DEFAULT_RETRIEVAL_K,
)
from src.core.request_models import Ticket
from src.core.conversation_control_models import ConversationControlInput
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
from src.conversation.conversation_controller import ConversationController
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
        conversation_controller: ConversationController,
        memory_store: InMemoryConversationStore,
        memory_loader: MemoryLoader,
        retrieval_policy: RetrievalPolicy,
        query_rewriter_agent: QueryRewriterAgent,
        retriever_tool: RetrieverTool,
        context_builder: ContextBuilder,
        summary_agent: SummaryAgent,
        response_agent: ResponseAgent,
        memory_agent: MemoryAgent,
    ) -> None:
        self.input_validator = input_validator
        self.conversation_state_loader = conversation_state_loader
        self.conversation_state_store = conversation_state_store
        self.conversation_controller = conversation_controller
        self.memory_store = memory_store
        self.memory_loader = memory_loader
        self.retrieval_policy = retrieval_policy
        self.query_rewriter_agent = query_rewriter_agent
        self.retriever_tool = retriever_tool
        self.context_builder = context_builder
        self.summary_agent = summary_agent
        self.response_agent = response_agent
        self.memory_agent = memory_agent

    def run_turn(self, ticket: Ticket) -> PipelineOutput:
        validated_ticket = self.input_validator.validate(ticket=ticket)

        previous_conversation_state = self.conversation_state_loader.load(
            ticket_id=validated_ticket.ticket_id
        )

        if previous_conversation_state is None:
            raise ValueError("ticket_id is required to run SupportPipeline")

        conversation_control_decision = self.conversation_controller.decide(
            control_input=ConversationControlInput(
                ticket=validated_ticket,
                conversation_state=previous_conversation_state,
            )
        )

        if (
            conversation_control_decision.force_escalation is True
            and conversation_control_decision.control_type == "escalate"
        ):
            predefined_escalation_response = PredefinedEscalationResponse(
                response=DEFAULT_ESCALATION_RESPONSE
            )

            new_conversation_state = self.conversation_controller.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                control_decision=conversation_control_decision,
                predefined_escalation_response=predefined_escalation_response,
            )

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=new_conversation_state,
            )

            return PipelineOutput(
                ticket=validated_ticket,
                previous_conversation_state=previous_conversation_state,
                conversation_control_decision=conversation_control_decision,
                conversation_state_after=new_conversation_state,
                response=predefined_escalation_response,
            )

        if conversation_control_decision.control_type == "closed":
            predefined_closing_response = PredefinedClosingResponse(
                response=DEFAULT_CLOSED_TICKET_RESPONSE
            )

            new_conversation_state = self.conversation_controller.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                control_decision=conversation_control_decision,
                predefined_closing_response=predefined_closing_response,
            )

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=new_conversation_state,
            )

            return PipelineOutput(
                ticket=validated_ticket,
                previous_conversation_state=previous_conversation_state,
                conversation_control_decision=conversation_control_decision,
                conversation_state_after=new_conversation_state,
                response=predefined_closing_response,
            )

        loaded_memory = self.memory_loader.load(
            ticket_id=validated_ticket.ticket_id
        )

        previous_conversation_memory = loaded_memory.memory
        previous_conversation_memory_text = (
            previous_conversation_memory.memory
            if previous_conversation_memory
            else None
        )

        if conversation_control_decision.allow_rag is False:
            response_output = self.response_agent.generate_response(
                response_input=ResponseInput(
                    ticket=validated_ticket,
                    memory_context=previous_conversation_memory_text,
                )
            )

            new_conversation_memory = self.memory_agent.update_memory(
                memory_update_input=MemoryUpdateInput(
                    ticket=validated_ticket,
                    previous_memory=previous_conversation_memory,
                    response=response_output,
                )
            )

            new_conversation_state = self.conversation_controller.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                control_decision=conversation_control_decision,
                response=response_output,
            )

            self.memory_store.save(
                ticket_id=validated_ticket.ticket_id,
                memory=new_conversation_memory,
            )

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=new_conversation_state,
            )

            return PipelineOutput(
                ticket=validated_ticket,
                previous_conversation_state=previous_conversation_state,
                conversation_control_decision=conversation_control_decision,
                conversation_state_after=new_conversation_state,
                previous_conversation_memory=previous_conversation_memory,
                response=response_output,
                memory_after=new_conversation_memory,
            )

        retrieval_policy_decision = self.retrieval_policy.decide(
            policy_input=RetrievalPolicyInput(
                ticket=validated_ticket,
                memory_context=previous_conversation_memory_text,
            )
        )

        if retrieval_policy_decision.use_rag is False:
            response_output = self.response_agent.generate_response(
                response_input=ResponseInput(
                    ticket=validated_ticket,
                    memory_context=previous_conversation_memory_text,
                )
            )

            new_conversation_memory = self.memory_agent.update_memory(
                memory_update_input=MemoryUpdateInput(
                    ticket=validated_ticket,
                    previous_memory=previous_conversation_memory,
                    response=response_output,
                )
            )

            new_conversation_state = self.conversation_controller.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                control_decision=conversation_control_decision,
                retrieval_decision=retrieval_policy_decision,
                response=response_output,
            )

            self.memory_store.save(
                ticket_id=validated_ticket.ticket_id,
                memory=new_conversation_memory,
            )

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=new_conversation_state,
            )

            return PipelineOutput(
                ticket=validated_ticket,
                previous_conversation_state=previous_conversation_state,
                conversation_control_decision=conversation_control_decision,
                conversation_state_after=new_conversation_state,
                previous_conversation_memory=previous_conversation_memory,
                retrieval_decision=retrieval_policy_decision,
                response=response_output,
                memory_after=new_conversation_memory,
            )

        query_rewriter_output = None

        if (
            retrieval_policy_decision.is_initial_turn is False
            and retrieval_policy_decision.use_memory is True
            and previous_conversation_memory_text
        ):
            query_rewriter_output = self.query_rewriter_agent.rewrite(
                query_rewriter_input=QueryRewriterInput(
                    current_description=validated_ticket.description,
                    memory_context=previous_conversation_memory_text,
                )
            )

        retrieval_tool_output = self.retriever_tool.invoke(
            retrieval_tool_input=RetrievalToolInput(
                ticket=validated_ticket,
                decision=retrieval_policy_decision,
                query=(
                    query_rewriter_output.optimized_query
                    if query_rewriter_output
                    else None
                ),
                k=DEFAULT_RETRIEVAL_K,
            )
        )

        if len(retrieval_tool_output.results) == 0:
            response_output = self.response_agent.generate_response(
                response_input=ResponseInput(
                    ticket=validated_ticket,
                    memory_context=previous_conversation_memory_text,
                )
            )

            new_conversation_memory = self.memory_agent.update_memory(
                memory_update_input=MemoryUpdateInput(
                    ticket=validated_ticket,
                    previous_memory=previous_conversation_memory,
                    response=response_output,
                )
            )

            new_conversation_state = self.conversation_controller.update_state(
                previous_state=previous_conversation_state,
                ticket=validated_ticket,
                control_decision=conversation_control_decision,
                retrieval_decision=retrieval_policy_decision,
                response=response_output,
            )

            self.memory_store.save(
                ticket_id=validated_ticket.ticket_id,
                memory=new_conversation_memory,
            )

            self.conversation_state_store.save(
                ticket_id=validated_ticket.ticket_id,
                state=new_conversation_state,
            )

            return PipelineOutput(
                ticket=validated_ticket,
                previous_conversation_state=previous_conversation_state,
                conversation_control_decision=conversation_control_decision,
                conversation_state_after=new_conversation_state,
                previous_conversation_memory=previous_conversation_memory,
                retrieval_decision=retrieval_policy_decision,
                query_rewriter_output=query_rewriter_output,
                retrieval_output=retrieval_tool_output,
                response=response_output,
                memory_after=new_conversation_memory,
            )

        built_context = self.context_builder.build(
            retrieval_results=retrieval_tool_output.results
        )

        summary_output = self.summary_agent.summarize(
            summary_input=SummaryInput(
                ticket=validated_ticket,
                built_context=built_context,
                memory_context=previous_conversation_memory_text,
            )
        )

        response_output = self.response_agent.generate_response(
            response_input=ResponseInput(
                ticket=validated_ticket,
                summary=summary_output,
                memory_context=previous_conversation_memory_text,
            )
        )

        new_conversation_memory = self.memory_agent.update_memory(
            memory_update_input=MemoryUpdateInput(
                ticket=validated_ticket,
                previous_memory=previous_conversation_memory,
                summary=summary_output,
                response=response_output,
            )
        )

        new_conversation_state = self.conversation_controller.update_state(
            previous_state=previous_conversation_state,
            ticket=validated_ticket,
            control_decision=conversation_control_decision,
            retrieval_decision=retrieval_policy_decision,
            response=response_output,
        )

        self.memory_store.save(
            ticket_id=validated_ticket.ticket_id,
            memory=new_conversation_memory,
        )

        self.conversation_state_store.save(
            ticket_id=validated_ticket.ticket_id,
            state=new_conversation_state,
        )

        return PipelineOutput(
            ticket=validated_ticket,
            previous_conversation_state=previous_conversation_state,
            conversation_control_decision=conversation_control_decision,
            conversation_state_after=new_conversation_state,
            previous_conversation_memory=previous_conversation_memory,
            retrieval_decision=retrieval_policy_decision,
            query_rewriter_output=query_rewriter_output,
            retrieval_output=retrieval_tool_output,
            built_context=built_context,
            summary=summary_output,
            response=response_output,
            memory_after=new_conversation_memory,
        )
