from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.core.context_models import BuiltContext
from src.core.conversation_state_models import ConversationState
from src.core.default_models import PredefinedClosingResponse, PredefinedEscalationResponse
from src.core.memory_models import ConversationMemory, LoadedMemory
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.summary_models import SummaryOutput
from src.graph.support_graph import build_support_graph


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def make_ticket(
    *,
    ticket_id: str = "ticket_1",
    turn_id: str = "turn_1",
    description: str = "My phone is overheating when charging.",
) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        turn_id=turn_id,
        source="web",
        description=description,
        domain="technical_support",
        subdomain="device_overheating",
        product="smartphone",
    )


def make_conversation_state(
    *,
    ticket_id: str = "ticket_1",
    turn_count: int = 0,
    rag_call_count: int = 0,
    status: str = "active",
    last_turn_id: str | None = None,
) -> ConversationState:
    now = datetime.now(timezone.utc).isoformat()

    return ConversationState(
        ticket_id=ticket_id,
        turn_count=turn_count,
        rag_call_count=rag_call_count,
        last_turn_id=last_turn_id,
        status=status,
        created_at=now,
        updated_at=now,
    )


def loaded_memory_empty() -> LoadedMemory:
    return LoadedMemory(
        has_memory=False,
        memory=None,
    )


def loaded_memory_with_content() -> LoadedMemory:
    return LoadedMemory(
        has_memory=True,
        memory=ConversationMemory(memory="User previously reported overheating."),
    )


def make_response_output(
    *,
    requires_escalation: bool = False,
    should_close: bool = False,
) -> ResponseOutput:
    return ResponseOutput(
        response="Please try these troubleshooting steps.",
        tone="professional",
        resolution_type="troubleshooting_steps",
        requires_escalation=requires_escalation,
        should_close=should_close,
        confidence=0.8,
        escalation_channel="none",
    )


def make_retrieval_decision(
    *,
    use_rag: bool,
    use_memory: bool,
    is_initial_turn: bool,
    retrieval_mode: str,
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type="metadata_and_description",
        reason="test decision",
    )


def retrieval_output_with_results() -> RetrievalToolOutput:
    return RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[SimpleNamespace(chunk_id="chunk_1", text="Relevant context")],
        total_results=1,
    )


def retrieval_output_without_results() -> RetrievalToolOutput:
    return RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[],
        total_results=0,
    )


def make_built_context() -> BuiltContext:
    return BuiltContext.model_construct(
        context_text="Relevant troubleshooting context.",
        results_used=[],
        truncated=False,
        total_chars=35,
    )


def make_summary() -> SummaryOutput:
    return SummaryOutput(
        problem="Phone overheats while charging.",
        context="The retrieved context mentions overheating troubleshooting.",
        intent="User wants a solution.",
    )


# ---------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------


class FakeInputValidator:
    def __init__(self):
        self.calls = 0

    def validate(self, ticket: Ticket) -> Ticket:
        self.calls += 1
        return ticket


class FakeConversationLoader:
    def __init__(self, state: ConversationState):
        self.state = state
        self.calls = 0

    def load(self, ticket_id: str | None) -> ConversationState:
        self.calls += 1
        return self.state


class FakeConversationStateStore:
    def __init__(self):
        self.calls = 0
        self.saved_ticket_id = None
        self.saved_state = None

    def save(self, ticket_id: str, state: ConversationState) -> None:
        self.calls += 1
        self.saved_ticket_id = ticket_id
        self.saved_state = state


class FakeConversationUpdater:
    def __init__(self):
        self.calls = 0
        self.last_kwargs = None

    def update_state(self, **kwargs) -> ConversationState:
        self.calls += 1
        self.last_kwargs = kwargs

        previous_state: ConversationState = kwargs["previous_state"]
        ticket: Ticket = kwargs["ticket"]
        retrieval_decision = kwargs.get("retrieval_decision")
        response = kwargs.get("response")
        predefined_escalation_response = kwargs.get("predefined_escalation_response")
        predefined_closing_response = kwargs.get("predefined_closing_response")

        status = "active"

        if predefined_closing_response is not None:
            status = "closed"
        elif predefined_escalation_response is not None:
            status = "escalated"
        elif response is not None and response.requires_escalation:
            status = "escalated"
        elif response is not None and response.should_close:
            status = "closed"

        rag_increment = 1 if retrieval_decision is not None and retrieval_decision.use_rag else 0

        return make_conversation_state(
            ticket_id=previous_state.ticket_id,
            turn_count=previous_state.turn_count + 1,
            rag_call_count=previous_state.rag_call_count + rag_increment,
            status=status,
            last_turn_id=ticket.turn_id,
        )


class FakeMemoryLoader:
    def __init__(self, loaded_memory: LoadedMemory):
        self.loaded_memory = loaded_memory
        self.calls = 0

    def load(self, ticket_id: str | None) -> LoadedMemory:
        self.calls += 1
        return self.loaded_memory


class FakeMemoryStore:
    def __init__(self):
        self.calls = 0
        self.saved_ticket_id = None
        self.saved_memory = None

    def save(self, ticket_id: str, memory: ConversationMemory) -> None:
        self.calls += 1
        self.saved_ticket_id = ticket_id
        self.saved_memory = memory


class FakeRetrievalPolicy:
    def __init__(self, decision: RetrievalPolicyDecision):
        self.decision = decision
        self.calls = 0

    def decide(self, policy_input):
        self.calls += 1
        return self.decision


class FakeQueryRewriterAgent:
    def __init__(self):
        self.calls = 0

    def rewrite(self, query_rewriter_input):
        self.calls += 1
        return QueryRewriterOutput(optimized_query="optimized overheating query")


class FakeRetrieverTool:
    def __init__(self, output: RetrievalToolOutput):
        self.output = output
        self.calls = 0
        self.last_input = None

    def invoke(self, retrieval_tool_input):
        self.calls += 1
        self.last_input = retrieval_tool_input
        return self.output


class FakeContextBuilder:
    def __init__(self):
        self.calls = 0

    def build(self, retrieval_results):
        self.calls += 1
        return make_built_context()


class FakeSummaryAgent:
    def __init__(self):
        self.calls = 0

    def summarize(self, summary_input):
        self.calls += 1
        return make_summary()


class FakeResponseAgent:
    def __init__(self, response: ResponseOutput | None = None):
        self.response = response or make_response_output()
        self.calls = 0

    def generate_response(self, response_input):
        self.calls += 1
        return self.response


class FakeMemoryAgent:
    def __init__(self):
        self.calls = 0

    def update_memory(self, memory_update_input):
        self.calls += 1
        return ConversationMemory(memory="Updated memory.")


@dataclass
class FakeDeps:
    input_validator: FakeInputValidator
    conversation_loader: FakeConversationLoader
    conversation_state_store: FakeConversationStateStore
    conversation_updater: FakeConversationUpdater
    memory_loader: FakeMemoryLoader
    memory_store: FakeMemoryStore
    retrieval_policy: FakeRetrievalPolicy
    query_rewriter_agent: FakeQueryRewriterAgent
    retriever_tool: FakeRetrieverTool
    context_builder: FakeContextBuilder
    summary_agent: FakeSummaryAgent
    response_agent: FakeResponseAgent
    memory_agent: FakeMemoryAgent


def make_deps(
    *,
    conversation_state: ConversationState | None = None,
    loaded_memory: LoadedMemory | None = None,
    retrieval_decision: RetrievalPolicyDecision | None = None,
    retrieval_output: RetrievalToolOutput | None = None,
    response: ResponseOutput | None = None,
) -> FakeDeps:
    return FakeDeps(
        input_validator=FakeInputValidator(),
        conversation_loader=FakeConversationLoader(
            conversation_state or make_conversation_state()
        ),
        conversation_state_store=FakeConversationStateStore(),
        conversation_updater=FakeConversationUpdater(),
        memory_loader=FakeMemoryLoader(loaded_memory or loaded_memory_empty()),
        memory_store=FakeMemoryStore(),
        retrieval_policy=FakeRetrievalPolicy(
            retrieval_decision
            or make_retrieval_decision(
                use_rag=False,
                use_memory=True,
                is_initial_turn=False,
                retrieval_mode="none",
            )
        ),
        query_rewriter_agent=FakeQueryRewriterAgent(),
        retriever_tool=FakeRetrieverTool(
            retrieval_output or retrieval_output_without_results()
        ),
        context_builder=FakeContextBuilder(),
        summary_agent=FakeSummaryAgent(),
        response_agent=FakeResponseAgent(response),
        memory_agent=FakeMemoryAgent(),
    )


def make_graph(deps: FakeDeps):
    return build_support_graph(
        input_validator=deps.input_validator,
        conversation_loader=deps.conversation_loader,
        conversation_state_store=deps.conversation_state_store,
        conversation_updater=deps.conversation_updater,
        memory_loader=deps.memory_loader,
        memory_store=deps.memory_store,
        retrieval_policy=deps.retrieval_policy,
        query_rewriter_agent=deps.query_rewriter_agent,
        retriever_tool=deps.retriever_tool,
        context_builder=deps.context_builder,
        summary_agent=deps.summary_agent,
        response_agent=deps.response_agent,
        memory_agent=deps.memory_agent,
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_support_graph_compiles():
    deps = make_deps()

    graph = make_graph(deps)

    assert graph is not None


def test_graph_already_closed_returns_predefined_response_and_skips_update_save_memory_and_rag():
    deps = make_deps(
        conversation_state=make_conversation_state(status="closed"),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert isinstance(final_state["response"], PredefinedClosingResponse)
    assert final_state["initial_route"] == "already_closed"

    assert deps.conversation_updater.calls == 0
    assert deps.conversation_state_store.calls == 0
    assert deps.memory_loader.calls == 0
    assert deps.memory_agent.calls == 0
    assert deps.memory_store.calls == 0
    assert deps.retrieval_policy.calls == 0
    assert deps.retriever_tool.calls == 0
    assert deps.response_agent.calls == 0


def test_graph_already_escalated_returns_predefined_response_and_skips_update_save_memory_and_rag():
    deps = make_deps(
        conversation_state=make_conversation_state(status="escalated"),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert isinstance(final_state["response"], PredefinedEscalationResponse)
    assert final_state["initial_route"] == "already_escalated"

    assert deps.conversation_updater.calls == 0
    assert deps.conversation_state_store.calls == 0
    assert deps.memory_loader.calls == 0
    assert deps.memory_agent.calls == 0
    assert deps.memory_store.calls == 0
    assert deps.retrieval_policy.calls == 0
    assert deps.retriever_tool.calls == 0
    assert deps.response_agent.calls == 0


def test_graph_force_escalation_updates_and_saves_state_without_memory_or_rag():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=5,
            rag_call_count=0,
        ),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert isinstance(final_state["response"], PredefinedEscalationResponse)
    assert final_state["initial_route"] == "force_escalation"
    assert final_state["conversation_state_after"].status == "escalated"

    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1

    assert deps.memory_loader.calls == 0
    assert deps.memory_agent.calls == 0
    assert deps.memory_store.calls == 0
    assert deps.retrieval_policy.calls == 0
    assert deps.retriever_tool.calls == 0
    assert deps.response_agent.calls == 0


def test_graph_rag_limit_reached_loads_memory_and_skips_retrieval_policy_and_rag():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=1,
            rag_call_count=3,
        ),
        loaded_memory=loaded_memory_with_content(),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert final_state["initial_route"] == "rag_limit_reached"
    assert isinstance(final_state["response"], ResponseOutput)
    assert final_state["summary"] is None if "summary" in final_state else True
    assert "retrieval_decision" not in final_state or final_state["retrieval_decision"] is None
    assert "retrieval_output" not in final_state or final_state["retrieval_output"] is None

    assert deps.memory_loader.calls == 1
    assert deps.response_agent.calls == 1
    assert deps.memory_agent.calls == 1
    assert deps.memory_store.calls == 1
    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1

    assert deps.retrieval_policy.calls == 0
    assert deps.query_rewriter_agent.calls == 0
    assert deps.retriever_tool.calls == 0
    assert deps.context_builder.calls == 0
    assert deps.summary_agent.calls == 0


def test_graph_active_no_rag_generates_response_updates_memory_and_state():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=1,
            rag_call_count=0,
        ),
        loaded_memory=loaded_memory_empty(),
        retrieval_decision=make_retrieval_decision(
            use_rag=False,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="none",
        ),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert final_state["initial_route"] == "active"
    assert final_state["retrieval_decision"].use_rag is False
    assert isinstance(final_state["response"], ResponseOutput)
    assert final_state["memory_after"].memory == "Updated memory."
    assert final_state["conversation_state_after"].status == "active"

    assert deps.memory_loader.calls == 1
    assert deps.retrieval_policy.calls == 1
    assert deps.response_agent.calls == 1
    assert deps.memory_agent.calls == 1
    assert deps.memory_store.calls == 1
    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1

    assert deps.query_rewriter_agent.calls == 0
    assert deps.retriever_tool.calls == 0
    assert deps.context_builder.calls == 0
    assert deps.summary_agent.calls == 0


def test_graph_active_rag_with_results_builds_context_summary_response_memory_and_state():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=0,
            rag_call_count=0,
        ),
        loaded_memory=loaded_memory_empty(),
        retrieval_decision=make_retrieval_decision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="hybrid",
        ),
        retrieval_output=retrieval_output_with_results(),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert final_state["initial_route"] == "active"
    assert final_state["retrieval_decision"].use_rag is True
    assert final_state["retrieval_output"].total_results == 1
    assert final_state["built_context"] is not None
    assert final_state["summary"] is not None
    assert isinstance(final_state["response"], ResponseOutput)
    assert final_state["memory_after"] is not None
    assert final_state["conversation_state_after"].rag_call_count == 1

    assert deps.retrieval_policy.calls == 1
    assert deps.retriever_tool.calls == 1
    assert deps.context_builder.calls == 1
    assert deps.summary_agent.calls == 1
    assert deps.response_agent.calls == 1
    assert deps.memory_agent.calls == 1
    assert deps.memory_store.calls == 1
    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1

    assert deps.query_rewriter_agent.calls == 0


def test_graph_active_rag_without_results_skips_context_and_summary():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=0,
            rag_call_count=0,
        ),
        loaded_memory=loaded_memory_empty(),
        retrieval_decision=make_retrieval_decision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="semantic",
        ),
        retrieval_output=retrieval_output_without_results(),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert final_state["initial_route"] == "active"
    assert final_state["retrieval_output"].total_results == 0
    assert "built_context" not in final_state or final_state["built_context"] is None
    assert "summary" not in final_state or final_state["summary"] is None
    assert isinstance(final_state["response"], ResponseOutput)

    assert deps.retrieval_policy.calls == 1
    assert deps.retriever_tool.calls == 1
    assert deps.response_agent.calls == 1
    assert deps.memory_agent.calls == 1
    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1

    assert deps.context_builder.calls == 0
    assert deps.summary_agent.calls == 0
    assert deps.query_rewriter_agent.calls == 0


def test_graph_active_followup_with_memory_uses_query_rewriter_before_retrieval():
    deps = make_deps(
        conversation_state=make_conversation_state(
            status="active",
            turn_count=2,
            rag_call_count=0,
        ),
        loaded_memory=loaded_memory_with_content(),
        retrieval_decision=make_retrieval_decision(
            use_rag=True,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="semantic",
        ),
        retrieval_output=retrieval_output_with_results(),
    )
    graph = make_graph(deps)

    final_state = graph.invoke({"ticket": make_ticket()})

    assert final_state["query_rewriter_output"].optimized_query == "optimized overheating query"
    assert deps.query_rewriter_agent.calls == 1
    assert deps.retriever_tool.calls == 1
    assert deps.retriever_tool.last_input.query == "optimized overheating query"

    assert deps.context_builder.calls == 1
    assert deps.summary_agent.calls == 1
    assert deps.response_agent.calls == 1
    assert deps.memory_agent.calls == 1
    assert deps.conversation_updater.calls == 1
    assert deps.conversation_state_store.calls == 1
