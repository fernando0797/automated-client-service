from __future__ import annotations

from typing import Any

import pytest

from src.pipeline.support_pipeline import SupportPipeline

from src.core.request_models import Ticket
from src.core.conversation_state_models import ConversationState
from src.core.memory_models import ConversationMemory
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.context_models import BuiltContext
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput
from src.core.default_models import (
    PredefinedClosingResponse,
    PredefinedEscalationResponse,
)

from src.conversation.conversation_state_store import InMemoryConversationStateStore
from src.conversation.conversation_state_loader import ConversationStateLoader
from src.conversation.conversation_controller import ConversationController

from src.memory.memory_store import InMemoryConversationStore
from src.memory.memory_loader import MemoryLoader


# =============================================================================
# Helpers
# =============================================================================


def make_ticket(
    description: str = "My iPhone battery drains very quickly after update.",
    ticket_id: str | None = "ticket_001",
    turn_id: str | None = "turn_001",
    source: str | None = "test",
    domain: str = "technical_support",
    subdomain: str = "battery_life",
    product: str = "iphone",
) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        turn_id=turn_id,
        source=source,
        description=description,
        domain=domain,
        subdomain=subdomain,
        product=product,
    )


def make_response(
    response: str = "Test response.",
    requires_escalation: bool = False,
) -> ResponseOutput:
    return ResponseOutput(
        response=response,
        tone="professional",
        resolution_type="escalation" if requires_escalation else "direct_solution",
        requires_escalation=requires_escalation,
        confidence=0.9,
        escalation_channel="support_ticket" if requires_escalation else "none",
    )


def make_retrieval_decision(
    use_rag: bool,
    use_memory: bool = False,
    is_initial_turn: bool = True,
    retrieval_mode: str = "none",
    decision_type: str = "insufficient_information",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type=decision_type,
        reason="Test retrieval decision.",
    )


def make_retrieval_output_with_results() -> RetrievalToolOutput:
    """
    Uses model_construct so the pipeline can test the non-empty retrieval branch
    without building real KnowledgeChunk / RetrievalResult objects.
    """
    return RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query="optimized query",
        results=[object()],
        total_results=1,
    )


def make_retrieval_output_without_results() -> RetrievalToolOutput:
    return RetrievalToolOutput(
        called=True,
        mode_used="semantic",
        optimized_query="optimized query",
        results=[],
        total_results=0,
    )


# =============================================================================
# Fake dependencies
# =============================================================================


class FakeInputValidator:
    def __init__(self) -> None:
        self.calls = 0

    def validate(self, ticket: Ticket) -> Ticket:
        self.calls += 1
        return ticket


class FakeRetrievalPolicy:
    def __init__(self, decision: RetrievalPolicyDecision) -> None:
        self.decision = decision
        self.calls = 0
        self.last_input = None

    def decide(self, policy_input: Any) -> RetrievalPolicyDecision:
        self.calls += 1
        self.last_input = policy_input
        return self.decision


class FakeQueryRewriterAgent:
    def __init__(self) -> None:
        self.calls = 0
        self.last_input = None

    def rewrite(self, query_rewriter_input: Any) -> QueryRewriterOutput:
        self.calls += 1
        self.last_input = query_rewriter_input
        return QueryRewriterOutput(
            optimized_query="optimized semantic query"
        )


class FakeRetrieverTool:
    def __init__(self, output: RetrievalToolOutput) -> None:
        self.output = output
        self.calls = 0
        self.last_input = None

    def invoke(self, retrieval_tool_input: Any) -> RetrievalToolOutput:
        self.calls += 1
        self.last_input = retrieval_tool_input
        return self.output


class FakeContextBuilder:
    def __init__(self) -> None:
        self.calls = 0
        self.last_results = None

    def build(self, retrieval_results: list[Any]) -> BuiltContext:
        self.calls += 1
        self.last_results = retrieval_results

        return BuiltContext.model_construct(
            context_text="Relevant retrieved context.",
            results_used=retrieval_results,
            total_chars=len("Relevant retrieved context."),
        )


class FakeSummaryAgent:
    def __init__(self) -> None:
        self.calls = 0
        self.last_input = None

    def summarize(self, summary_input: Any) -> SummaryOutput:
        self.calls += 1
        self.last_input = summary_input

        return SummaryOutput(
            problem="User reports a battery issue.",
            context="Retrieved context explains battery troubleshooting.",
            intent="Provide troubleshooting steps.",
        )


class FakeResponseAgent:
    def __init__(self, response: ResponseOutput | None = None) -> None:
        self.response = response or make_response()
        self.calls = 0
        self.last_input = None

    def generate_response(self, response_input: Any) -> ResponseOutput:
        self.calls += 1
        self.last_input = response_input
        return self.response


class FakeMemoryAgent:
    def __init__(self, memory_text: str = "Updated memory.") -> None:
        self.memory_text = memory_text
        self.calls = 0
        self.last_input = None

    def update_memory(self, memory_update_input: Any) -> ConversationMemory:
        self.calls += 1
        self.last_input = memory_update_input
        return ConversationMemory(memory=self.memory_text)


# =============================================================================
# Pipeline factory
# =============================================================================


@pytest.fixture
def conversation_state_store() -> InMemoryConversationStateStore:
    return InMemoryConversationStateStore()


@pytest.fixture
def conversation_state_loader(
    conversation_state_store: InMemoryConversationStateStore,
) -> ConversationStateLoader:
    return ConversationStateLoader(store=conversation_state_store)


@pytest.fixture
def conversation_controller() -> ConversationController:
    return ConversationController(
        max_turns_per_ticket=8,
        max_rag_calls_per_ticket=4,
    )


@pytest.fixture
def memory_store() -> InMemoryConversationStore:
    return InMemoryConversationStore()


@pytest.fixture
def memory_loader(
    memory_store: InMemoryConversationStore,
) -> MemoryLoader:
    return MemoryLoader(store=memory_store)


def build_pipeline(
    *,
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
    retrieval_decision: RetrievalPolicyDecision | None = None,
    retrieval_output: RetrievalToolOutput | None = None,
    response_output: ResponseOutput | None = None,
) -> tuple[
    SupportPipeline,
    FakeInputValidator,
    FakeRetrievalPolicy,
    FakeQueryRewriterAgent,
    FakeRetrieverTool,
    FakeContextBuilder,
    FakeSummaryAgent,
    FakeResponseAgent,
    FakeMemoryAgent,
]:
    input_validator = FakeInputValidator()

    retrieval_policy = FakeRetrievalPolicy(
        decision=retrieval_decision
        or make_retrieval_decision(
            use_rag=False,
            use_memory=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="insufficient_information",
        )
    )

    query_rewriter_agent = FakeQueryRewriterAgent()

    retriever_tool = FakeRetrieverTool(
        output=retrieval_output or make_retrieval_output_without_results()
    )

    context_builder = FakeContextBuilder()
    summary_agent = FakeSummaryAgent()
    response_agent = FakeResponseAgent(response=response_output)
    memory_agent = FakeMemoryAgent()

    pipeline = SupportPipeline(
        input_validator=input_validator,
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_policy=retrieval_policy,
        query_rewriter_agent=query_rewriter_agent,
        retriever_tool=retriever_tool,
        context_builder=context_builder,
        summary_agent=summary_agent,
        response_agent=response_agent,
        memory_agent=memory_agent,
    )

    return (
        pipeline,
        input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    )


# =============================================================================
# Pre-control branches
# =============================================================================


def test_pipeline_closing_turn_skips_memory_retrieval_and_response_agent(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    (
        pipeline,
        input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
    )

    ticket = make_ticket(description="Gracias", turn_id="turn_001")

    output = pipeline.run_turn(ticket)

    assert input_validator.calls == 1
    assert output.conversation_control_decision.control_type == "closed"
    assert isinstance(output.response, PredefinedClosingResponse)
    assert output.conversation_state_after is not None
    assert output.conversation_state_after.status == "closed"

    assert retrieval_policy.calls == 0
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 0
    assert context_builder.calls == 0
    assert summary_agent.calls == 0
    assert response_agent.calls == 0
    assert memory_agent.calls == 0

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.status == "closed"


def test_pipeline_escalates_when_max_turns_reached_and_skips_flow(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    existing_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=8,
        rag_call_count=0,
        last_turn_id="turn_008",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )
    conversation_state_store.save("ticket_001", existing_state)

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
    )

    ticket = make_ticket(
        description="The issue is still happening.",
        turn_id="turn_009",
    )

    output = pipeline.run_turn(ticket)

    assert output.conversation_control_decision.control_type == "escalate"
    assert output.conversation_control_decision.force_escalation is True
    assert isinstance(output.response, PredefinedEscalationResponse)
    assert output.conversation_state_after is not None
    assert output.conversation_state_after.status == "escalated"

    assert retrieval_policy.calls == 0
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 0
    assert context_builder.calls == 0
    assert summary_agent.calls == 0
    assert response_agent.calls == 0
    assert memory_agent.calls == 0

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.status == "escalated"


def test_pipeline_raises_when_ticket_id_is_missing(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    (
        pipeline,
        *_,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
    )

    ticket = make_ticket(ticket_id=None)

    with pytest.raises(
        ValueError,
        match="ticket_id is required to run SupportPipeline",
    ):
        pipeline.run_turn(ticket)


# =============================================================================
# allow_rag=False branch
# =============================================================================


def test_pipeline_max_rag_calls_loads_memory_and_skips_retrieval_policy(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    existing_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=2,
        rag_call_count=4,
        last_turn_id="turn_002",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )
    conversation_state_store.save("ticket_001", existing_state)

    memory_store.save(
        "ticket_001",
        ConversationMemory(memory="Previous issue was about battery drain."),
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
    )

    ticket = make_ticket(
        description="What should I do next?",
        turn_id="turn_003",
    )

    output = pipeline.run_turn(ticket)

    assert output.conversation_control_decision.control_type == "max_rag_calls_reached"
    assert output.conversation_control_decision.allow_rag is False
    assert output.previous_conversation_memory is not None
    assert output.previous_conversation_memory.memory == (
        "Previous issue was about battery drain."
    )
    assert isinstance(output.response, ResponseOutput)
    assert output.memory_after is not None

    assert retrieval_policy.calls == 0
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 0
    assert context_builder.calls == 0
    assert summary_agent.calls == 0
    assert response_agent.calls == 1
    assert memory_agent.calls == 1

    saved_memory = memory_store.get("ticket_001")
    assert saved_memory is not None
    assert saved_memory.memory == "Updated memory."

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.rag_call_count == 4
    assert saved_state.turn_count == 3


# =============================================================================
# RetrievalPolicy use_rag=False branch
# =============================================================================


def test_pipeline_retrieval_policy_no_rag_calls_response_and_memory_only(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        use_memory=True,
        is_initial_turn=False,
        retrieval_mode="none",
        decision_type="clarification",
    )

    memory_store.save(
        "ticket_001",
        ConversationMemory(memory="Previous assistant answer."),
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
    )

    ticket = make_ticket(
        description="Can you explain it more simply?",
        turn_id="turn_002",
    )

    output = pipeline.run_turn(ticket)

    assert output.retrieval_decision == retrieval_decision
    assert output.previous_conversation_memory is not None
    assert output.previous_conversation_memory.memory == "Previous assistant answer."
    assert isinstance(output.response, ResponseOutput)
    assert output.memory_after is not None

    assert retrieval_policy.calls == 1
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 0
    assert context_builder.calls == 0
    assert summary_agent.calls == 0
    assert response_agent.calls == 1
    assert memory_agent.calls == 1

    saved_memory = memory_store.get("ticket_001")
    assert saved_memory is not None
    assert saved_memory.memory == "Updated memory."


# =============================================================================
# RAG initial turn branch
# =============================================================================


def test_pipeline_initial_rag_skips_query_rewriter_and_summarizes_results(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=True,
        use_memory=False,
        is_initial_turn=True,
        retrieval_mode="hybrid",
        decision_type="metadata_and_description",
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
        retrieval_output=make_retrieval_output_with_results(),
    )

    ticket = make_ticket(turn_id="turn_001")

    output = pipeline.run_turn(ticket)

    assert output.retrieval_decision == retrieval_decision
    assert output.query_rewriter_output is None
    assert output.retrieval_output is not None
    assert output.built_context is not None
    assert output.summary is not None
    assert isinstance(output.response, ResponseOutput)
    assert output.memory_after is not None

    assert retrieval_policy.calls == 1
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 1
    assert context_builder.calls == 1
    assert summary_agent.calls == 1
    assert response_agent.calls == 1
    assert memory_agent.calls == 1

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.rag_call_count == 1


# =============================================================================
# RAG later turn with memory branch
# =============================================================================


def test_pipeline_later_rag_with_memory_calls_query_rewriter(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    existing_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=1,
        rag_call_count=0,
        last_turn_id="turn_001",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )
    conversation_state_store.save("ticket_001", existing_state)

    memory_store.save(
        "ticket_001",
        ConversationMemory(
            memory="Previous issue was about iPhone battery drain."),
    )

    retrieval_decision = make_retrieval_decision(
        use_rag=True,
        use_memory=True,
        is_initial_turn=False,
        retrieval_mode="semantic",
        decision_type="problem_update",
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
        retrieval_output=make_retrieval_output_with_results(),
    )

    ticket = make_ticket(
        description="Now my MacBook is not charging.",
        turn_id="turn_002",
    )

    output = pipeline.run_turn(ticket)

    assert output.query_rewriter_output is not None
    assert output.query_rewriter_output.optimized_query == "optimized semantic query"
    assert output.retrieval_output is not None
    assert output.summary is not None

    assert retrieval_policy.calls == 1
    assert query_rewriter_agent.calls == 1
    assert retriever_tool.calls == 1
    assert context_builder.calls == 1
    assert summary_agent.calls == 1
    assert response_agent.calls == 1
    assert memory_agent.calls == 1

    assert retriever_tool.last_input.query == "optimized semantic query"

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.turn_count == 2
    assert saved_state.rag_call_count == 1


def test_pipeline_later_rag_without_memory_skips_query_rewriter(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    existing_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=1,
        rag_call_count=0,
        last_turn_id="turn_001",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )
    conversation_state_store.save("ticket_001", existing_state)

    retrieval_decision = make_retrieval_decision(
        use_rag=True,
        use_memory=True,
        is_initial_turn=False,
        retrieval_mode="semantic",
        decision_type="problem_update",
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
        retrieval_output=make_retrieval_output_with_results(),
    )

    ticket = make_ticket(
        description="Now my MacBook is not charging.",
        turn_id="turn_002",
    )

    output = pipeline.run_turn(ticket)

    assert output.query_rewriter_output is None
    assert retriever_tool.last_input.query is None

    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 1
    assert context_builder.calls == 1
    assert summary_agent.calls == 1
    assert response_agent.calls == 1
    assert memory_agent.calls == 1


# =============================================================================
# RAG with no retrieval results branch
# =============================================================================


def test_pipeline_rag_with_no_results_skips_context_builder_and_summary_agent(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=True,
        use_memory=False,
        is_initial_turn=True,
        retrieval_mode="hybrid",
        decision_type="metadata_and_description",
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        query_rewriter_agent,
        retriever_tool,
        context_builder,
        summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
        retrieval_output=make_retrieval_output_without_results(),
    )

    ticket = make_ticket(turn_id="turn_001")

    output = pipeline.run_turn(ticket)

    assert output.retrieval_output is not None
    assert output.retrieval_output.results == []
    assert output.built_context is None
    assert output.summary is None
    assert isinstance(output.response, ResponseOutput)

    assert retrieval_policy.calls == 1
    assert query_rewriter_agent.calls == 0
    assert retriever_tool.calls == 1
    assert context_builder.calls == 0
    assert summary_agent.calls == 0
    assert response_agent.calls == 1
    assert memory_agent.calls == 1


# =============================================================================
# Response-driven escalation branch
# =============================================================================


def test_pipeline_response_agent_escalation_updates_state_to_escalated(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    response_output = make_response(
        response="This case should be escalated.",
        requires_escalation=True,
    )

    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        use_memory=False,
        is_initial_turn=False,
        retrieval_mode="none",
        decision_type="insufficient_information",
    )

    (
        pipeline,
        _input_validator,
        retrieval_policy,
        _query_rewriter_agent,
        _retriever_tool,
        _context_builder,
        _summary_agent,
        response_agent,
        memory_agent,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
        response_output=response_output,
    )

    ticket = make_ticket(
        description="The device smells burned and shuts down.",
        turn_id="turn_001",
    )

    output = pipeline.run_turn(ticket)

    assert isinstance(output.response, ResponseOutput)
    assert output.response.requires_escalation is True
    assert output.conversation_state_after is not None
    assert output.conversation_state_after.status == "escalated"

    assert response_agent.calls == 1
    assert memory_agent.calls == 1

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.status == "escalated"


# =============================================================================
# Turn deduplication / persistence
# =============================================================================


def test_pipeline_does_not_increment_turn_count_for_repeated_turn_id(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    existing_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=1,
        rag_call_count=0,
        last_turn_id="turn_001",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )
    conversation_state_store.save("ticket_001", existing_state)

    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        use_memory=False,
        is_initial_turn=False,
        retrieval_mode="none",
        decision_type="insufficient_information",
    )

    (
        pipeline,
        *_,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
    )

    ticket = make_ticket(
        description="Same turn retried.",
        turn_id="turn_001",
    )

    output = pipeline.run_turn(ticket)

    assert output.conversation_state_after is not None
    assert output.conversation_state_after.turn_count == 1

    saved_state = conversation_state_store.get("ticket_001")
    assert saved_state is not None
    assert saved_state.turn_count == 1


def test_pipeline_persists_memory_for_next_turn(
    conversation_state_loader: ConversationStateLoader,
    conversation_state_store: InMemoryConversationStateStore,
    conversation_controller: ConversationController,
    memory_store: InMemoryConversationStore,
    memory_loader: MemoryLoader,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        use_memory=False,
        is_initial_turn=False,
        retrieval_mode="none",
        decision_type="insufficient_information",
    )

    (
        pipeline,
        *_,
    ) = build_pipeline(
        conversation_state_loader=conversation_state_loader,
        conversation_state_store=conversation_state_store,
        conversation_controller=conversation_controller,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_decision=retrieval_decision,
    )

    ticket = make_ticket(
        description="The battery still drains.",
        turn_id="turn_001",
    )

    output = pipeline.run_turn(ticket)

    assert output.memory_after is not None
    assert output.memory_after.memory == "Updated memory."

    saved_memory = memory_store.get("ticket_001")
    assert saved_memory is not None
    assert saved_memory.memory == "Updated memory."
