from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from src.core.request_models import Ticket
from src.core.memory_models import ConversationMemory, LoadedMemory, MemoryUpdateInput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.context_models import BuiltContext
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput
from src.core.pipeline_models import PipelineOutput

from src.memory.memory_store import InMemoryConversationStore
from src.memory.memory_loader import MemoryLoader
from src.pipeline.support_pipeline import SupportPipeline


# ============================================================
# Helpers
# ============================================================

def make_ticket(
    ticket_id: str | None = "ticket-001",
    turn_id: str | None = "turn-001",
    description: str = "My iPhone battery drains quickly after the latest update.",
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


def make_decision(
    use_rag: bool,
    is_initial_turn: bool,
    retrieval_mode: str = "none",
    use_memory: bool = False,
    decision_type: str = "insufficient_information",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type=decision_type,
        reason="Test decision.",
    )


def make_response_output(
    text: str = "Please check Battery Health and review background activity.",
) -> ResponseOutput:
    return ResponseOutput(
        response=text,
        tone="professional",
        resolution_type="troubleshooting_steps",
        requires_escalation=False,
        confidence=0.8,
        escalation_channel="none",
    )


def make_summary_output() -> SummaryOutput:
    return SummaryOutput(
        problem="The user reports fast iPhone battery drain.",
        context="The issue may relate to battery health, updates, or background activity.",
        intent="The user wants troubleshooting help.",
    )


def make_memory(text: str = "Existing memory for this ticket.") -> ConversationMemory:
    return ConversationMemory(memory=text)


def make_retrieval_output_with_results() -> RetrievalToolOutput:
    # model_construct avoids needing a real RetrievalResult object.
    # The pipeline only checks whether results is truthy and passes it to ContextBuilder.
    return RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[object()],
        total_results=1,
    )


def make_retrieval_output_without_results() -> RetrievalToolOutput:
    return RetrievalToolOutput(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[],
        total_results=0,
    )


# ============================================================
# Fake dependencies
# ============================================================

class FakeInputValidator:
    def __init__(self, validated_ticket: Ticket | None = None):
        self.validated_ticket = validated_ticket
        self.called_with = None
        self.call_count = 0

    def validate(self, ticket: Ticket) -> Ticket:
        self.call_count += 1
        self.called_with = ticket
        return self.validated_ticket or ticket


class FakeMemoryLoader:
    def __init__(self, loaded_memory: LoadedMemory):
        self.loaded_memory = loaded_memory
        self.called_with_ticket_id = None
        self.call_count = 0

    def load(self, ticket_id: str | None) -> LoadedMemory:
        self.call_count += 1
        self.called_with_ticket_id = ticket_id
        return self.loaded_memory


class FakeRetrievalPolicy:
    def __init__(self, decision: RetrievalPolicyDecision):
        self.decision = decision
        self.called_with = None
        self.call_count = 0

    def decide(self, retrieval_policy_input):
        self.call_count += 1
        self.called_with = retrieval_policy_input
        return self.decision


class FakeQueryRewriterAgent:
    def __init__(self, optimized_query: str = "iphone battery drain after update"):
        self.output = QueryRewriterOutput(optimized_query=optimized_query)
        self.called_with = None
        self.call_count = 0

    def rewrite(self, query_rewriter_input):
        self.call_count += 1
        self.called_with = query_rewriter_input
        return self.output


class FakeRetrieverTool:
    def __init__(self, output: RetrievalToolOutput):
        self.output = output
        self.called_with = None
        self.call_count = 0

    def invoke(self, retrieval_tool_input):
        self.call_count += 1
        self.called_with = retrieval_tool_input
        return self.output


class FakeContextBuilder:
    def __init__(self):
        self.output = BuiltContext(
            context_text="Battery drain troubleshooting context.",
            results_used=[],
            total_chars=len("Battery drain troubleshooting context."),
        )
        self.called_with = None
        self.call_count = 0

    def build(self, retrieval_results):
        self.call_count += 1
        self.called_with = retrieval_results
        return self.output


class FakeSummaryAgent:
    def __init__(self):
        self.output = make_summary_output()
        self.called_with = None
        self.call_count = 0

    def summarize(self, summary_input):
        self.call_count += 1
        self.called_with = summary_input
        return self.output


class FakeResponseAgent:
    def __init__(self):
        self.output = make_response_output()
        self.called_with = None
        self.call_count = 0

    def generate_response(self, response_input):
        self.call_count += 1
        self.called_with = response_input
        return self.output


class FakeMemoryAgent:
    def __init__(self):
        self.output = ConversationMemory(
            memory="Updated memory after this support turn."
        )
        self.called_with = None
        self.call_count = 0

    def update_memory(self, memory_update_input):
        self.call_count += 1
        self.called_with = memory_update_input
        return self.output


@dataclass
class PipelineDeps:
    pipeline: SupportPipeline
    input_validator: FakeInputValidator
    memory_store: InMemoryConversationStore
    memory_loader: FakeMemoryLoader
    retrieval_policy: FakeRetrievalPolicy
    query_rewriter_agent: FakeQueryRewriterAgent
    retriever_tool: FakeRetrieverTool
    context_builder: FakeContextBuilder
    summary_agent: FakeSummaryAgent
    response_agent: FakeResponseAgent
    memory_agent: FakeMemoryAgent


def build_pipeline_deps(
    decision: RetrievalPolicyDecision,
    loaded_memory: LoadedMemory | None = None,
    retrieval_output: RetrievalToolOutput | None = None,
    validated_ticket: Ticket | None = None,
) -> PipelineDeps:
    input_validator = FakeInputValidator(validated_ticket=validated_ticket)

    memory_store = InMemoryConversationStore()
    memory_loader = FakeMemoryLoader(
        loaded_memory=loaded_memory
        or LoadedMemory(has_memory=False, memory=None)
    )

    retrieval_policy = FakeRetrievalPolicy(decision=decision)
    query_rewriter_agent = FakeQueryRewriterAgent()
    retriever_tool = FakeRetrieverTool(
        output=retrieval_output or make_retrieval_output_without_results()
    )
    context_builder = FakeContextBuilder()
    summary_agent = FakeSummaryAgent()
    response_agent = FakeResponseAgent()
    memory_agent = FakeMemoryAgent()

    pipeline = SupportPipeline(
        input_validator=input_validator,
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

    return PipelineDeps(
        pipeline=pipeline,
        input_validator=input_validator,
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


# ============================================================
# 1. No RAG branch
# ============================================================

def test_pipeline_no_rag_skips_retrieval_summary_and_rewriter():
    ticket = make_ticket()

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=False,
            is_initial_turn=False,
            retrieval_mode="none",
            use_memory=False,
            decision_type="follow_up",
        )
    )

    result = deps.pipeline.run_turn(ticket)

    assert isinstance(result, PipelineOutput)

    assert deps.input_validator.call_count == 1
    assert deps.memory_loader.call_count == 1
    assert deps.retrieval_policy.call_count == 1

    assert deps.query_rewriter_agent.call_count == 0
    assert deps.retriever_tool.call_count == 0
    assert deps.context_builder.call_count == 0
    assert deps.summary_agent.call_count == 0

    assert deps.response_agent.call_count == 1
    assert deps.memory_agent.call_count == 1

    assert result.summary is None
    assert result.retrieval_output is None
    assert result.built_context is None
    assert result.query_rewriter_output is None

    assert deps.response_agent.called_with.summary is None
    assert deps.memory_agent.called_with.summary is None


def test_pipeline_no_rag_saves_updated_memory_when_ticket_id_exists():
    ticket = make_ticket(ticket_id="ticket-001")

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="follow_up",
        )
    )

    result = deps.pipeline.run_turn(ticket)

    stored_memory = deps.memory_store.get("ticket-001")

    assert stored_memory == result.memory_after
    assert stored_memory == deps.memory_agent.output


# ============================================================
# 2. RAG initial turn branch
# ============================================================

def test_pipeline_rag_initial_turn_skips_query_rewriter_and_summarizes_results():
    ticket = make_ticket(turn_id="turn-001")

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            is_initial_turn=True,
            retrieval_mode="hybrid",
            decision_type="metadata_and_description",
        ),
        retrieval_output=make_retrieval_output_with_results(),
    )

    result = deps.pipeline.run_turn(ticket)

    assert deps.query_rewriter_agent.call_count == 0
    assert deps.retriever_tool.call_count == 1
    assert deps.context_builder.call_count == 1
    assert deps.summary_agent.call_count == 1
    assert deps.response_agent.call_count == 1
    assert deps.memory_agent.call_count == 1

    assert deps.retriever_tool.called_with.query is None
    assert result.summary == deps.summary_agent.output
    assert deps.response_agent.called_with.summary == deps.summary_agent.output
    assert deps.memory_agent.called_with.summary == deps.summary_agent.output
    assert deps.retriever_tool.called_with.k == 5


def test_pipeline_rag_initial_turn_passes_results_to_context_builder():
    ticket = make_ticket()

    retrieval_output = make_retrieval_output_with_results()

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            is_initial_turn=True,
            retrieval_mode="hybrid",
            decision_type="metadata_and_description",
        ),
        retrieval_output=retrieval_output,
    )

    deps.pipeline.run_turn(ticket)

    assert deps.context_builder.called_with == retrieval_output.results


# ============================================================
# 3. RAG follow-up branch with memory
# ============================================================

def test_pipeline_rag_follow_up_with_memory_uses_query_rewriter():
    ticket = make_ticket(turn_id="turn-002")
    previous_memory = make_memory(
        "The user has an unresolved iPhone battery issue after an update."
    )

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
            decision_type="problem_update",
        ),
        loaded_memory=LoadedMemory(
            has_memory=True,
            memory=previous_memory,
        ),
        retrieval_output=make_retrieval_output_with_results(),
    )

    result = deps.pipeline.run_turn(ticket)

    assert deps.query_rewriter_agent.call_count == 1
    assert deps.query_rewriter_agent.called_with.current_description == ticket.description
    assert deps.query_rewriter_agent.called_with.memory_context == previous_memory.memory

    assert deps.retriever_tool.call_count == 1
    assert deps.retriever_tool.called_with.query == deps.query_rewriter_agent.output.optimized_query

    assert result.query_rewriter_output == deps.query_rewriter_agent.output
    assert result.memory_before == previous_memory
    assert deps.retriever_tool.called_with.k == 5


def test_pipeline_rag_follow_up_with_memory_passes_memory_to_policy_summary_response_and_memory_agent():
    ticket = make_ticket(turn_id="turn-002")
    previous_memory = make_memory("Previous useful memory.")

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
            decision_type="problem_update",
        ),
        loaded_memory=LoadedMemory(
            has_memory=True,
            memory=previous_memory,
        ),
        retrieval_output=make_retrieval_output_with_results(),
    )

    deps.pipeline.run_turn(ticket)

    assert deps.retrieval_policy.called_with.memory_context == previous_memory.memory
    assert deps.summary_agent.called_with.memory_context == previous_memory.memory
    assert deps.response_agent.called_with.memory_context == previous_memory.memory
    assert deps.memory_agent.called_with.previous_memory == previous_memory


# ============================================================
# 4. RAG follow-up branch without memory
# ============================================================

def test_pipeline_rag_follow_up_without_memory_skips_query_rewriter():
    ticket = make_ticket(turn_id="turn-002")

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=False,
            retrieval_mode="semantic",
            decision_type="problem_update",
        ),
        loaded_memory=LoadedMemory(
            has_memory=False,
            memory=None,
        ),
        retrieval_output=make_retrieval_output_with_results(),
    )

    result = deps.pipeline.run_turn(ticket)

    assert deps.query_rewriter_agent.call_count == 0
    assert deps.retriever_tool.call_count == 1
    assert deps.retriever_tool.called_with.query is None

    assert result.query_rewriter_output is None
    assert result.summary == deps.summary_agent.output


# ============================================================
# 5. RAG decided but retriever returns no results
# ============================================================

def test_pipeline_rag_with_no_results_skips_context_builder_and_summary_agent():
    ticket = make_ticket()

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=True,
            is_initial_turn=True,
            retrieval_mode="semantic",
            decision_type="description_only",
        ),
        retrieval_output=make_retrieval_output_without_results(),
    )

    result = deps.pipeline.run_turn(ticket)

    assert deps.retriever_tool.call_count == 1
    assert deps.context_builder.call_count == 0
    assert deps.summary_agent.call_count == 0

    assert result.retrieval_output is not None
    assert result.retrieval_output.results == []
    assert result.built_context is None
    assert result.summary is None

    assert deps.response_agent.called_with.summary is None
    assert deps.memory_agent.called_with.summary is None


# ============================================================
# 6. Validation and persistence boundaries
# ============================================================

def test_pipeline_uses_validated_ticket_after_input_validation():
    original_ticket = make_ticket(
        description="Original description.",
        domain="technical_support",
    )

    validated_ticket = make_ticket(
        description="Validated description.",
    )

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="follow_up",
        ),
        validated_ticket=validated_ticket,
    )

    result = deps.pipeline.run_turn(original_ticket)

    assert deps.input_validator.called_with == original_ticket

    assert deps.memory_loader.called_with_ticket_id == validated_ticket.ticket_id
    assert deps.retrieval_policy.called_with.ticket == validated_ticket
    assert deps.response_agent.called_with.ticket == validated_ticket
    assert deps.memory_agent.called_with.ticket == validated_ticket

    assert result.ticket == validated_ticket


def test_pipeline_does_not_save_memory_when_ticket_id_is_missing():
    ticket = make_ticket(ticket_id=None)

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="follow_up",
        )
    )

    result = deps.pipeline.run_turn(ticket)

    assert result.memory_after == deps.memory_agent.output
    assert deps.memory_store._memories == {}


# ============================================================
# 7. Integration-style test with real memory store + loader
# ============================================================

def test_pipeline_integration_memory_is_available_on_second_turn():
    memory_store = InMemoryConversationStore()
    memory_loader = MemoryLoader(memory_store)

    input_validator = FakeInputValidator()
    retrieval_policy = FakeRetrievalPolicy(
        make_decision(
            use_rag=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="follow_up",
        )
    )
    query_rewriter_agent = FakeQueryRewriterAgent()
    retriever_tool = FakeRetrieverTool(make_retrieval_output_without_results())
    context_builder = FakeContextBuilder()
    summary_agent = FakeSummaryAgent()
    response_agent = FakeResponseAgent()
    memory_agent = FakeMemoryAgent()

    pipeline = SupportPipeline(
        input_validator=input_validator,
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

    first_ticket = make_ticket(
        ticket_id="ticket-001",
        turn_id="turn-001",
        description="My iPhone battery drains quickly.",
    )

    first_result = pipeline.run_turn(first_ticket)

    assert first_result.memory_before is None
    assert memory_store.exists("ticket-001") is True

    second_ticket = make_ticket(
        ticket_id="ticket-001",
        turn_id="turn-002",
        description="It still drains fast after restarting.",
    )

    second_result = pipeline.run_turn(second_ticket)

    assert second_result.memory_before == first_result.memory_after
    assert retrieval_policy.called_with.memory_context == first_result.memory_after.memory
    assert response_agent.called_with.memory_context == first_result.memory_after.memory
    assert memory_agent.called_with.previous_memory == first_result.memory_after


# ============================================================
# 8. Optional live LLM smoke test
# ============================================================

requires_live_llm = pytest.mark.skipif(
    os.getenv("RUN_LIVE_LLM_TESTS") != "1",
    reason="Set RUN_LIVE_LLM_TESTS=1 to run live pipeline smoke tests.",
)


@pytest.mark.live_llm
@requires_live_llm
def test_pipeline_live_smoke_no_rag_with_real_response_and_memory_agents():
    """
    This is intentionally narrow.

    It does not test the full production RAG stack, because that would require
    real retriever/vector dependencies. It verifies that the conditional pipeline
    can call real ResponseAgent and MemoryAgent when use_rag=False.
    """
    from src.agents.response_agent import ResponseAgent
    from src.agents.memory_agent import MemoryAgent

    ticket = make_ticket(
        ticket_id="ticket-live-001",
        turn_id="turn-001",
        description="My iPhone battery drains quickly after the latest update.",
    )

    memory_store = InMemoryConversationStore()
    memory_loader = MemoryLoader(memory_store)

    deps = build_pipeline_deps(
        decision=make_decision(
            use_rag=False,
            is_initial_turn=True,
            retrieval_mode="none",
            decision_type="insufficient_information",
        ),
        loaded_memory=LoadedMemory(has_memory=False, memory=None),
    )

    pipeline = SupportPipeline(
        input_validator=deps.input_validator,
        memory_store=memory_store,
        memory_loader=memory_loader,
        retrieval_policy=deps.retrieval_policy,
        query_rewriter_agent=deps.query_rewriter_agent,
        retriever_tool=deps.retriever_tool,
        context_builder=deps.context_builder,
        summary_agent=deps.summary_agent,
        response_agent=ResponseAgent(),
        memory_agent=MemoryAgent(),
    )

    result = pipeline.run_turn(ticket)

    assert isinstance(result, PipelineOutput)
    assert result.summary is None
    assert result.response.response.strip()
    assert len(result.response.response) <= 3000
    assert result.memory_after is not None
    assert result.memory_after.memory.strip()
    assert len(result.memory_after.memory) <= 1200
    assert memory_store.exists("ticket-live-001") is True
