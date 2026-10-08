from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.core.conversation_state_models import ConversationState
from src.core.memory_models import ConversationMemory
from src.core.pipeline_models import PipelineOutput
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.persistence.database import create_db_session
from src.persistence.models import ConversationTraceORM
from src.persistence.repositories.turn_trace_repository import SQLTraceStore


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def unique_ticket_id() -> str:
    return f"test_ticket_{uuid4().hex}"


def make_ticket(
    *,
    ticket_id: str,
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


def make_response_output(
    *,
    requires_escalation: bool = False,
    should_close: bool = False,
) -> ResponseOutput:
    return ResponseOutput(
        response="Please check the charger and avoid using the phone while charging.",
        tone="professional",
        resolution_type="troubleshooting_steps",
        requires_escalation=requires_escalation,
        should_close=should_close,
        confidence=0.8,
        escalation_channel="none",
    )


def make_retrieval_decision(
    *,
    use_rag: bool = True,
    use_memory: bool = False,
    is_initial_turn: bool = True,
    retrieval_mode: str = "semantic",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type="metadata_and_description",
        reason="test decision",
    )


def make_pipeline_output(
    *,
    ticket_id: str,
    turn_id: str = "turn_1",
    use_rag: bool = True,
    initial_route: str = "active",
    nodes_executed: list[str] | None = None,
) -> PipelineOutput:
    ticket = make_ticket(
        ticket_id=ticket_id,
        turn_id=turn_id,
    )

    previous_state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=0,
        rag_call_count=0,
        last_turn_id=None,
        status="active",
    )

    state_after = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=1,
        rag_call_count=1 if use_rag else 0,
        last_turn_id=turn_id,
        status="active",
    )

    retrieval_decision = (
        make_retrieval_decision(use_rag=True)
        if use_rag
        else make_retrieval_decision(
            use_rag=False,
            use_memory=True,
            is_initial_turn=False,
            retrieval_mode="none",
        )
    )

    return PipelineOutput(
        ticket=ticket,
        initial_route=initial_route,
        previous_conversation_state=previous_state,
        conversation_state_after=state_after,
        previous_conversation_memory=ConversationMemory(
            memory="The user previously reported overheating."
        ),
        memory_after=ConversationMemory(
            memory="The user reported overheating while charging."
        ),
        retrieval_decision=retrieval_decision,
        query_rewriter_output=None,
        retrieval_output=None,
        built_context=None,
        summary=None,
        response=make_response_output(),
        nodes_executed=nodes_executed
        or [
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
        ],
    )


@pytest.fixture
def db_session() -> Session:
    db = create_db_session()

    try:
        yield db
    finally:
        db.close()


def cleanup_traces(db: Session, ticket_id: str) -> None:
    rows = (
        db.query(ConversationTraceORM)
        .filter(ConversationTraceORM.ticket_id == ticket_id)
        .all()
    )

    for row in rows:
        db.delete(row)

    db.commit()


def get_traces(db: Session, ticket_id: str) -> list[ConversationTraceORM]:
    return (
        db.query(ConversationTraceORM)
        .filter(ConversationTraceORM.ticket_id == ticket_id)
        .order_by(ConversationTraceORM.id.asc())
        .all()
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_sql_trace_store_save_creates_trace_row(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(ticket_id=ticket_id)

    try:
        store.save(pipeline_output)

        rows = get_traces(db_session, ticket_id)

        assert len(rows) == 1

        row = rows[0]

        assert row.ticket_id == ticket_id
        assert row.turn_id == "turn_1"
        assert row.initial_route == "active"
        assert row.use_rag is True

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_ticket_json(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(ticket_id=ticket_id)

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.input_ticket_json["ticket_id"] == ticket_id
        assert row.input_ticket_json["turn_id"] == "turn_1"
        assert row.input_ticket_json["description"] == (
            "My phone is overheating when charging."
        )
        assert row.input_ticket_json["domain"] == "technical_support"
        assert row.input_ticket_json["subdomain"] == "device_overheating"
        assert row.input_ticket_json["product"] == "smartphone"

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_state_json(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(ticket_id=ticket_id)

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.previous_state_json["ticket_id"] == ticket_id
        assert row.previous_state_json["turn_count"] == 0
        assert row.previous_state_json["rag_call_count"] == 0
        assert row.previous_state_json["status"] == "active"

        assert row.state_after_json["ticket_id"] == ticket_id
        assert row.state_after_json["turn_count"] == 1
        assert row.state_after_json["rag_call_count"] == 1
        assert row.state_after_json["last_turn_id"] == "turn_1"
        assert row.state_after_json["status"] == "active"

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_memory_json(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(ticket_id=ticket_id)

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.previous_memory_json["memory"] == (
            "The user previously reported overheating."
        )
        assert row.memory_after_json["memory"] == (
            "The user reported overheating while charging."
        )

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_retrieval_decision_json(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(
        ticket_id=ticket_id,
        use_rag=True,
    )

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.retrieval_decision_json["use_rag"] is True
        assert row.retrieval_decision_json["retrieval_mode"] == "semantic"
        assert row.retrieval_decision_json["decision_type"] == (
            "metadata_and_description"
        )

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_sets_use_rag_false_when_decision_use_rag_false(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(
        ticket_id=ticket_id,
        use_rag=False,
    )

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.use_rag is False
        assert row.retrieval_decision_json["use_rag"] is False
        assert row.retrieval_decision_json["retrieval_mode"] == "none"

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_response_json(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    pipeline_output = make_pipeline_output(ticket_id=ticket_id)

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.response_json["response"] == (
            "Please check the charger and avoid using the phone while charging."
        )
        assert row.response_json["tone"] == "professional"
        assert row.response_json["resolution_type"] == "troubleshooting_steps"
        assert row.response_json["requires_escalation"] is False
        assert row.response_json["should_close"] is False
        assert row.response_json["escalation_channel"] == "none"

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_serializes_nodes_executed(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    nodes_executed = [
        "validate_input_ticket",
        "load_conversation_state",
        "classify_initial_route",
        "load_memory",
        "generate_response_output",
        "save_conversation_state",
    ]

    pipeline_output = make_pipeline_output(
        ticket_id=ticket_id,
        nodes_executed=nodes_executed,
    )

    try:
        store.save(pipeline_output)

        row = get_traces(db_session, ticket_id)[0]

        assert row.nodes_executed == nodes_executed
        assert len(row.nodes_executed) == 6

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_save_creates_one_row_per_turn(db_session: Session):
    ticket_id = unique_ticket_id()
    store = SQLTraceStore(db_session)

    first_output = make_pipeline_output(
        ticket_id=ticket_id,
        turn_id="turn_1",
    )
    second_output = make_pipeline_output(
        ticket_id=ticket_id,
        turn_id="turn_2",
    )

    try:
        store.save(first_output)
        store.save(second_output)

        rows = get_traces(db_session, ticket_id)

        assert len(rows) == 2
        assert rows[0].turn_id == "turn_1"
        assert rows[1].turn_id == "turn_2"

    finally:
        cleanup_traces(db_session, ticket_id)


def test_sql_trace_store_persists_between_sessions():
    ticket_id = unique_ticket_id()

    first_db = create_db_session()
    try:
        first_store = SQLTraceStore(first_db)
        pipeline_output = make_pipeline_output(ticket_id=ticket_id)

        first_store.save(pipeline_output)

    finally:
        first_db.close()

    second_db = create_db_session()
    try:
        rows = get_traces(second_db, ticket_id)

        assert len(rows) == 1
        assert rows[0].ticket_id == ticket_id
        assert rows[0].turn_id == "turn_1"
        assert rows[0].response_json["response"] == (
            "Please check the charger and avoid using the phone while charging."
        )

    finally:
        cleanup_traces(second_db, ticket_id)
        second_db.close()
