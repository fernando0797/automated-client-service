from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.agents.memory_agent import MemoryAgent
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.agents.response_agent import ResponseAgent
from src.agents.summary_agent import SummaryAgent
from src.conversation.conversation_updater import ConversationUpdater
from src.core.context_models import BuiltContext
from src.core.conversation_state_models import ConversationState
from src.core.default_models import PredefinedClosingResponse
from src.core.memory_models import ConversationMemory
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.summary_models import SummaryOutput
from src.graph.graph_runner import SupportGraphRunner
from src.persistence.database import create_db_session
from src.persistence.models import (
    ConversationMemoryORM,
    ConversationStateORM,
    ConversationTraceORM,
)
from src.persistence.repositories.conversation_memory_repository import (
    SQLConversationMemoryStore,
)
from src.persistence.repositories.conversation_state_repository import (
    SQLConversationStateStore,
)
from src.persistence.repositories.turn_trace_repository import SQLTraceStore
from src.rag.context_builder import ContextBuilder
from src.rag.retrieval_policy import RetrievalPolicy
from src.tools.retriever_tool import RetrieverTool


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def unique_ticket_id() -> str:
    return f"test_ticket_{uuid4().hex}"


def make_ticket(
    *,
    ticket_id: str,
    turn_id: str,
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
    ticket_id: str,
    turn_count: int = 0,
    rag_call_count: int = 0,
    last_turn_id: str | None = None,
    status: str = "active",
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


def make_no_rag_decision() -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=False,
        use_memory=True,
        is_initial_turn=False,
        retrieval_mode="none",
        decision_type="follow_up",
        reason="test no rag decision",
    )


def make_rag_decision() -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=True,
        use_memory=False,
        is_initial_turn=True,
        retrieval_mode="semantic",
        decision_type="metadata_and_description",
        reason="test rag decision",
    )


def cleanup_ticket_data(db: Session, ticket_id: str) -> None:
    trace_rows = (
        db.query(ConversationTraceORM)
        .filter(ConversationTraceORM.ticket_id == ticket_id)
        .all()
    )

    for row in trace_rows:
        db.delete(row)

    memory_row = db.get(ConversationMemoryORM, ticket_id)

    if memory_row is not None:
        db.delete(memory_row)

    state_row = db.get(ConversationStateORM, ticket_id)

    if state_row is not None:
        db.delete(state_row)

    db.commit()


def get_state_row(db: Session, ticket_id: str) -> ConversationStateORM | None:
    return db.get(ConversationStateORM, ticket_id)


def get_memory_row(db: Session, ticket_id: str) -> ConversationMemoryORM | None:
    return db.get(ConversationMemoryORM, ticket_id)


def get_trace_rows(db: Session, ticket_id: str) -> list[ConversationTraceORM]:
    return (
        db.query(ConversationTraceORM)
        .filter(ConversationTraceORM.ticket_id == ticket_id)
        .order_by(ConversationTraceORM.id.asc())
        .all()
    )


# ---------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------


class FakeInputValidator():
    def validate(self, ticket: Ticket) -> Ticket:
        return ticket


class FakeRetrievalPolicy(RetrievalPolicy):
    def __init__(self, decision: RetrievalPolicyDecision):
        self.decision = decision
        self.calls = 0

    def decide(self, policy_input):
        self.calls += 1
        return self.decision


class FakeQueryRewriterAgent(QueryRewriterAgent):
    def __init__(self):
        self.calls = 0

    def rewrite(self, query_rewriter_input):
        self.calls += 1
        return QueryRewriterOutput(
            optimized_query="optimized overheating troubleshooting query"
        )


class FakeRetrieverTool(RetrieverTool):
    def __init__(self, output: RetrievalToolOutput | None = None):
        self.output = output or RetrievalToolOutput.model_construct(
            called=True,
            mode_used="semantic",
            optimized_query=None,
            results=[],
            total_results=0,
        )
        self.calls = 0

    def invoke(self, retrieval_tool_input):
        self.calls += 1
        return self.output


class FakeContextBuilder(ContextBuilder):
    def __init__(self):
        self.calls = 0

    def build(self, retrieval_results):
        self.calls += 1
        return BuiltContext.model_construct(
            context_text="Relevant troubleshooting context.",
            results_used=[],
            truncated=False,
            total_chars=35,
        )


class FakeSummaryAgent(SummaryAgent):
    def __init__(self):
        self.calls = 0

    def summarize(self, summary_input):
        self.calls += 1
        return SummaryOutput(
            problem="Phone overheats while charging.",
            context="Retrieved context mentions overheating troubleshooting.",
            intent="User wants a solution.",
        )


class FakeResponseAgent(ResponseAgent):
    def __init__(self):
        self.calls = 0

    def generate_response(self, response_input):
        self.calls += 1
        return ResponseOutput(
            response="Please check the charger and avoid using the phone while charging.",
            tone="professional",
            resolution_type="troubleshooting_steps",
            requires_escalation=False,
            should_close=False,
            confidence=0.8,
            escalation_channel="none",
        )


class FakeMemoryAgent(MemoryAgent):
    def __init__(self):
        self.calls = 0

    def update_memory(self, memory_update_input):
        self.calls += 1
        turn_id = memory_update_input.ticket.turn_id
        return ConversationMemory(memory=f"Memory after {turn_id}.")


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


@pytest.fixture
def db_session():
    db = create_db_session()

    try:
        yield db
    finally:
        db.close()


def make_runner(
    *,
    db: Session,
    retrieval_decision: RetrievalPolicyDecision | None = None,
) -> SupportGraphRunner:
    state_store = SQLConversationStateStore(db)
    memory_store = SQLConversationMemoryStore(db)
    trace_store = SQLTraceStore(db)

    return SupportGraphRunner(
        input_validator=FakeInputValidator(),
        conversation_state_store=state_store,
        conversation_updater=ConversationUpdater(),
        memory_store=memory_store,
        retrieval_policy=FakeRetrievalPolicy(
            retrieval_decision or make_no_rag_decision()
        ),
        query_rewriter_agent=FakeQueryRewriterAgent(),
        retriever_tool=FakeRetrieverTool(),
        context_builder=FakeContextBuilder(),
        summary_agent=FakeSummaryAgent(),
        response_agent=FakeResponseAgent(),
        memory_agent=FakeMemoryAgent(),
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
        trace_store=trace_store,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_support_graph_sql_persists_state_memory_and_trace_between_two_turns(
    db_session: Session,
):
    ticket_id = unique_ticket_id()

    try:
        runner = make_runner(db=db_session)

        first_output = runner.run(
            make_ticket(
                ticket_id=ticket_id,
                turn_id="turn_1",
                description="My phone overheats while charging.",
            )
        )

        assert first_output.previous_conversation_state.turn_count == 0
        assert first_output.conversation_state_after.turn_count == 1
        assert first_output.conversation_state_after.rag_call_count == 0
        assert first_output.memory_after is not None
        assert first_output.memory_after.memory == "Memory after turn_1."

        second_output = runner.run(
            make_ticket(
                ticket_id=ticket_id,
                turn_id="turn_2",
                description="It still happens after changing the charger.",
            )
        )

        assert second_output.previous_conversation_state.turn_count == 1
        assert second_output.conversation_state_after.turn_count == 2
        assert second_output.conversation_state_after.rag_call_count == 0

        assert second_output.previous_conversation_memory is not None
        assert second_output.previous_conversation_memory.memory == "Memory after turn_1."

        state_row = get_state_row(db_session, ticket_id)
        memory_row = get_memory_row(db_session, ticket_id)
        trace_rows = get_trace_rows(db_session, ticket_id)

        assert state_row is not None
        assert state_row.turn_count == 2
        assert state_row.rag_call_count == 0
        assert state_row.last_turn_id == "turn_2"
        assert state_row.status == "active"

        assert memory_row is not None
        assert memory_row.memory == "Memory after turn_2."

        assert len(trace_rows) == 2
        assert trace_rows[0].turn_id == "turn_1"
        assert trace_rows[1].turn_id == "turn_2"

    finally:
        cleanup_ticket_data(db_session, ticket_id)


def test_support_graph_sql_trace_contains_route_nodes_response_and_state(
    db_session: Session,
):
    ticket_id = unique_ticket_id()

    try:
        runner = make_runner(db=db_session)

        output = runner.run(
            make_ticket(
                ticket_id=ticket_id,
                turn_id="turn_1",
            )
        )

        trace_rows = get_trace_rows(db_session, ticket_id)

        assert len(trace_rows) == 1

        trace = trace_rows[0]

        assert trace.ticket_id == ticket_id
        assert trace.turn_id == "turn_1"
        assert trace.initial_route == output.initial_route
        assert trace.initial_route == "active"
        assert trace.use_rag is False

        assert trace.input_ticket_json["ticket_id"] == ticket_id
        assert trace.input_ticket_json["turn_id"] == "turn_1"

        assert trace.previous_state_json["turn_count"] == 0
        assert trace.state_after_json["turn_count"] == 1
        assert trace.state_after_json["last_turn_id"] == "turn_1"

        assert trace.response_json["response"] == (
            "Please check the charger and avoid using the phone while charging."
        )
        assert trace.response_json["requires_escalation"] is False
        assert trace.response_json["should_close"] is False

        assert trace.nodes_executed == output.nodes_executed
        assert trace.nodes_executed == [
            "validate_input_ticket",
            "load_conversation_state",
            "classify_initial_route",
            "load_memory",
            "retrieval_policy_decision",
            "generate_response_output",
            "generate_new_memory",
            "save_conversation_memory",
            "update_conversation",
            "save_conversation_state",
        ]

    finally:
        cleanup_ticket_data(db_session, ticket_id)


def test_support_graph_sql_already_closed_branch_is_traced_without_state_or_memory_update(
    db_session: Session,
):
    ticket_id = unique_ticket_id()

    try:
        state_store = SQLConversationStateStore(db_session)

        closed_state = make_conversation_state(
            ticket_id=ticket_id,
            turn_count=2,
            rag_call_count=1,
            last_turn_id="turn_2",
            status="closed",
        )

        state_store.save(ticket_id=ticket_id, state=closed_state)

        runner = make_runner(db=db_session)

        output = runner.run(
            make_ticket(
                ticket_id=ticket_id,
                turn_id="turn_3",
                description="Thanks, that is solved.",
            )
        )

        assert isinstance(output.response, PredefinedClosingResponse)
        assert output.initial_route == "already_closed"
        assert output.conversation_state_after.status == "closed"

        state_row = get_state_row(db_session, ticket_id)
        memory_row = get_memory_row(db_session, ticket_id)
        trace_rows = get_trace_rows(db_session, ticket_id)

        assert state_row is not None
        assert state_row.status == "closed"
        assert state_row.turn_count == 2
        assert state_row.last_turn_id == "turn_2"

        assert memory_row is None

        assert len(trace_rows) == 1

        trace = trace_rows[0]

        assert trace.initial_route == "already_closed"
        assert trace.turn_id == "turn_3"
        assert trace.use_rag is False
        assert trace.previous_state_json["status"] == "closed"
        assert trace.state_after_json["status"] == "closed"
        assert trace.memory_after_json is None
        assert trace.retrieval_decision_json is None

        assert trace.nodes_executed == [
            "validate_input_ticket",
            "load_conversation_state",
            "classify_initial_route",
            "already_closed_response",
        ]

    finally:
        cleanup_ticket_data(db_session, ticket_id)
