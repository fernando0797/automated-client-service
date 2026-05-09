from __future__ import annotations

from typing import Callable

from src.graph.graph_state import SupportGraphState, InitialRoute
from src.validation.input_validator import InputValidator
from src.conversation.conversation_state_loader import ConversationStateLoader
from src.conversation.conversation_updater import ConversationUpdater
from src.conversation.conversation_state_store import InMemoryConversationStateStore
from src.memory.memory_loader import MemoryLoader
from src.agents.response_agent import ResponseAgent
from src.agents.memory_agent import MemoryAgent
from src.rag.retrieval_policy import RetrievalPolicy
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.tools.retriever_tool import RetrieverTool
from src.rag.context_builder import ContextBuilder
from src.agents.summary_agent import SummaryAgent
from src.memory.memory_store import InMemoryConversationStore

from src.core.default_models import PredefinedClosingResponse, PredefinedEscalationResponse
from src.core.response_models import ResponseOutput, ResponseInput
from src.core.memory_models import MemoryUpdateInput
from src.core.retrieval_policy_models import RetrievalPolicyInput
from src.core.query_rewriter_models import QueryRewriterInput
from src.core.retrieval_tool_models import RetrievalToolInput
from src.core.summary_models import SummaryInput
from src.core.config import DEFAULT_ALREADY_ESCALATED_RESPONSE, DEFAULT_CLOSED_TICKET_RESPONSE, DEFAULT_FORCE_ESCALATION_RESPONSE, DEFAULT_RETRIEVAL_K


def make_validate_input_ticket_node(input_validator: InputValidator) -> Callable[[SupportGraphState], dict]:

    def validate_input_ticket_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")

        if ticket is None:
            raise ValueError("ticket is required before validating ticket")

        validated_ticket = input_validator.validate(ticket=ticket)

        return {"ticket": validated_ticket}

    return validate_input_ticket_node


def make_load_conversation_state_node(conversation_loader: ConversationStateLoader) -> Callable[[SupportGraphState], dict]:

    def load_conversation_state_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")

        if ticket is None:
            raise ValueError("ticket is required before loading previous conversation state")

        previous_conversation_state = conversation_loader.load(ticket.ticket_id)

        return {"previous_conversation_state": previous_conversation_state}

    return load_conversation_state_node


def make_classify_initial_route_node(*, max_turns_per_ticket: int, max_rag_calls_per_ticket: int) -> Callable[[SupportGraphState], dict]:

    def classify_initial_route_node(state: SupportGraphState) -> dict:
        conversation_state = state.get("previous_conversation_state")

        if conversation_state is None:
            raise ValueError("previous_conversation_state is required before classifying initial route.")

        if conversation_state.status == "closed":
            initial_route: InitialRoute = "already_closed"

        elif conversation_state.status == "escalated":
            initial_route = "already_escalated"

        elif conversation_state.turn_count >= max_turns_per_ticket:
            initial_route = "force_escalation"

        elif conversation_state.rag_call_count >= max_rag_calls_per_ticket:
            initial_route = "rag_limit_reached"

        else:
            initial_route = "active"

        return {"initial_route": initial_route}

    return classify_initial_route_node


def already_closed_response_node(state: SupportGraphState) -> dict:
    return {"response": PredefinedClosingResponse(response=DEFAULT_CLOSED_TICKET_RESPONSE)}


def already_escalated_response_node(state: SupportGraphState) -> dict:
    return {"response": PredefinedEscalationResponse(response=DEFAULT_ALREADY_ESCALATED_RESPONSE)}


def force_escalation_response_node(state: SupportGraphState) -> dict:
    return {"response": PredefinedEscalationResponse(response=DEFAULT_FORCE_ESCALATION_RESPONSE)}


def make_update_conversation_node(conversation_updater: ConversationUpdater) -> Callable[[SupportGraphState], dict]:

    def update_conversation_node(state: SupportGraphState) -> dict:
        previous_conversation_state = state.get("previous_conversation_state")
        ticket = state.get("ticket")
        retrieval_decision = state.get("retrieval_decision")
        raw_response = state.get("response")

        if previous_conversation_state is None:
            raise ValueError("previous_conversation_state is required before updating state")

        if ticket is None:
            raise ValueError("ticket is required before updating state")

        if raw_response is None:
            raise ValueError("response is required before updating state")

        response = raw_response if isinstance(raw_response, ResponseOutput) else None
        predefined_closing_response = raw_response if isinstance(raw_response, PredefinedClosingResponse) else None
        predefined_escalation_response = raw_response if isinstance(
            raw_response, PredefinedEscalationResponse) else None

        new_conversation_state = conversation_updater.update_state(previous_state=previous_conversation_state, ticket=ticket, retrieval_decision=retrieval_decision,
                                                                   response=response, predefined_closing_response=predefined_closing_response,
                                                                   predefined_escalation_response=predefined_escalation_response)
        return {"conversation_state_after": new_conversation_state}

    return update_conversation_node


def make_save_conversation_state_node(conversation_state_store: InMemoryConversationStateStore) -> Callable[[SupportGraphState], dict]:

    def save_conversation_state_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        conversation_state = state.get("conversation_state_after")

        if ticket is None:
            raise ValueError("ticket is required before saving conversation state")

        if conversation_state is None:
            raise ValueError("conversation_state_after is required before saving state")

        conversation_state_store.save(ticket_id=ticket.ticket_id, state=conversation_state)

        return {}

    return save_conversation_state_node


def make_save_conversation_memory_node(memory_store: InMemoryConversationStore) -> Callable[[SupportGraphState], dict]:

    def save_conversation_memory_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        memory_after = state.get("memory_after")

        if ticket is None:
            raise ValueError("ticket is required before saving conversation state")

        if memory_after is None:
            raise ValueError("a new memory is required before saving the memory")

        memory_store.save(ticket_id=ticket.ticket_id, memory=memory_after)

        return {}

    return save_conversation_memory_node


def make_load_memory_node(memory_loader: MemoryLoader) -> Callable[[SupportGraphState], dict]:

    def load_memory_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")

        if ticket is None:
            raise ValueError("ticket is required before loading previous memory")

        loaded_memory = memory_loader.load(ticket_id=ticket.ticket_id)

        return {"previous_conversation_memory": loaded_memory}

    return load_memory_node


def make_generate_response_output_node(response_agent: ResponseAgent) -> Callable[[SupportGraphState], dict]:

    def generate_response_output_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        summary = state.get("summary")
        loaded_memory = state.get("previous_conversation_memory")

        if ticket is None:
            raise ValueError("ticket is required before generating a response output")

        if loaded_memory is None:
            raise ValueError("previous_conversation_memory is required before generating a response output")

        memory_text = loaded_memory.memory.memory if loaded_memory.has_memory else None
        response = response_agent.generate_response(response_input=ResponseInput(
            ticket=ticket, summary=summary, memory_context=memory_text))

        return {"response": response}

    return generate_response_output_node


def make_generate_new_memory_node(memory_agent: MemoryAgent) -> Callable[[SupportGraphState], dict]:

    def generate_new_memory_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        loaded_memory = state.get("previous_conversation_memory")
        summary = state.get("summary")
        response = state.get("response")

        if ticket is None:
            raise ValueError("ticket is required before updating memory")

        if loaded_memory is None:
            raise ValueError("previous_conversation_memory is required before updating memory")

        if not isinstance(response, ResponseOutput):
            raise ValueError("state response must be a ResponseOutput object if new memory generation is wanted")

        previous_memory = loaded_memory.memory

        new_conversation_memory = memory_agent.update_memory(memory_update_input=MemoryUpdateInput(
            ticket=ticket, previous_memory=previous_memory, summary=summary, response=response))

        return {"memory_after": new_conversation_memory}

    return generate_new_memory_node


def make_retrieval_policy_decision_node(retrieval_policy: RetrievalPolicy) -> Callable[[SupportGraphState], dict]:

    def retrieval_policy_decision_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        loaded_memory = state.get("previous_conversation_memory")

        if ticket is None:
            raise ValueError("ticket is required before generating a retrieval policy decision")

        if loaded_memory is None:
            raise ValueError("previous_conversation_memory is required before generating a retrieval policy decision")

        memory_text = loaded_memory.memory.memory if loaded_memory.has_memory else None

        decision = retrieval_policy.decide(policy_input=RetrievalPolicyInput(ticket=ticket, memory_context=memory_text))

        return {"retrieval_decision": decision}

    return retrieval_policy_decision_node


def make_rewrite_query_node(query_rewriter_agent: QueryRewriterAgent) -> Callable[[SupportGraphState], dict]:

    def rewrite_query_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        loaded_memory = state.get("previous_conversation_memory")

        if ticket is None:
            raise ValueError("ticket is required before rewriting the query")

        if loaded_memory is None:
            raise ValueError("previous_conversation_memory is required before rewriting the query")

        if loaded_memory.has_memory is False:
            raise ValueError("Query Rewriter Agent requires previous memory to generate output")

        current_description = ticket.description
        memory_text = loaded_memory.memory.memory

        query_rewriter_output = query_rewriter_agent.rewrite(query_rewriter_input=QueryRewriterInput(
            current_description=current_description, memory_context=memory_text))

        return {"query_rewriter_output": query_rewriter_output}

    return rewrite_query_node


def make_retrieve_results_tool(retriever_tool: RetrieverTool) -> Callable[[SupportGraphState], dict]:

    def retrieve_results_tool(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        retrieval_decision = state.get("retrieval_decision")
        query_rewriter_output = state.get("query_rewriter_output")

        if ticket is None:
            raise ValueError("ticket is required before retrieving results")

        if retrieval_decision is None:
            raise ValueError("retrieval_decision is required before retrieving results")

        if query_rewriter_output:
            query = query_rewriter_output.optimized_query
        else:
            query = ticket.description

        retrieval_output = retriever_tool.invoke(retrieval_tool_input=RetrievalToolInput(
            ticket=ticket, decision=retrieval_decision, query=query, k=DEFAULT_RETRIEVAL_K))

        return {"retrieval_output": retrieval_output}

    return retrieve_results_tool


def make_build_context_node(context_builder: ContextBuilder) -> Callable[[SupportGraphState], dict]:

    def build_context_node(state: SupportGraphState) -> dict:
        retrieval_output = state.get("retrieval_output")

        if retrieval_output is None:
            raise ValueError("retrieval_output is required before building the context")

        retrieval_results = retrieval_output.results

        if len(retrieval_results) == 0:
            raise ValueError("retrieval_results must not be empty for the context to be built")

        built_context = context_builder.build(retrieval_results=retrieval_results)

        return {"built_context": built_context}

    return build_context_node


def make_build_summary_node(summary_agent: SummaryAgent) -> Callable[[SupportGraphState], dict]:

    def build_summary_node(state: SupportGraphState) -> dict:
        ticket = state.get("ticket")
        built_context = state.get("built_context")
        loaded_memory = state.get("previous_conversation_memory")

        if ticket is None:
            raise ValueError("ticket is required before building summary")

        if built_context is None:
            raise ValueError("built_context is required before building summary")

        if loaded_memory is None:
            raise ValueError("previous_conversation_memory is required before building summary")

        memory_text = loaded_memory.memory.memory if loaded_memory.has_memory else None

        summary = summary_agent.summarize(summary_input=SummaryInput(
            ticket=ticket, built_context=built_context, memory_context=memory_text))

        return {"summary": summary}

    return build_summary_node
