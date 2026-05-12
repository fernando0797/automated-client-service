from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.core.conversation_state_models import ConversationState
from src.persistence.database import create_db_session
from src.persistence.models import ConversationStateORM
from src.persistence.repositories.conversation_state_repository import (
    SQLConversationStateStore,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def unique_ticket_id() -> str:
    return f"test_ticket_{uuid4().hex}"


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


@pytest.fixture
def db_session() -> Session:
    db = create_db_session()

    try:
        yield db
    finally:
        db.close()


def cleanup_state(db: Session, ticket_id: str) -> None:
    row = db.get(ConversationStateORM, ticket_id)

    if row is not None:
        db.delete(row)
        db.commit()


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_sql_conversation_state_store_get_returns_none_when_ticket_id_is_none(
    db_session: Session,
):
    store = SQLConversationStateStore(db_session)

    result = store.get(None)

    assert result is None


def test_sql_conversation_state_store_get_returns_none_when_ticket_id_is_empty(
    db_session: Session,
):
    store = SQLConversationStateStore(db_session)

    result = store.get("   ")

    assert result is None


def test_sql_conversation_state_store_get_returns_none_when_state_does_not_exist(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationStateStore(db_session)

    result = store.get(ticket_id)

    assert result is None


def test_sql_conversation_state_store_save_creates_new_state(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationStateStore(db_session)

    state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=1,
        rag_call_count=1,
        last_turn_id="turn_1",
        status="active",
    )

    try:
        store.save(ticket_id=ticket_id, state=state)

        loaded = store.get(ticket_id)

        assert loaded is not None
        assert loaded.ticket_id == ticket_id
        assert loaded.turn_count == 1
        assert loaded.rag_call_count == 1
        assert loaded.last_turn_id == "turn_1"
        assert loaded.status == "active"

    finally:
        cleanup_state(db_session, ticket_id)


def test_sql_conversation_state_store_save_updates_existing_state(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationStateStore(db_session)

    initial_state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=1,
        rag_call_count=0,
        last_turn_id="turn_1",
        status="active",
    )

    updated_state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=2,
        rag_call_count=1,
        last_turn_id="turn_2",
        status="active",
    )

    try:
        store.save(ticket_id=ticket_id, state=initial_state)
        store.save(ticket_id=ticket_id, state=updated_state)

        loaded = store.get(ticket_id)

        assert loaded is not None
        assert loaded.ticket_id == ticket_id
        assert loaded.turn_count == 2
        assert loaded.rag_call_count == 1
        assert loaded.last_turn_id == "turn_2"
        assert loaded.status == "active"

    finally:
        cleanup_state(db_session, ticket_id)


def test_sql_conversation_state_store_persists_between_sessions():
    ticket_id = unique_ticket_id()

    first_db = create_db_session()
    try:
        first_store = SQLConversationStateStore(first_db)

        state = make_conversation_state(
            ticket_id=ticket_id,
            turn_count=3,
            rag_call_count=2,
            last_turn_id="turn_3",
            status="active",
        )

        first_store.save(ticket_id=ticket_id, state=state)

    finally:
        first_db.close()

    second_db = create_db_session()
    try:
        second_store = SQLConversationStateStore(second_db)

        loaded = second_store.get(ticket_id)

        assert loaded is not None
        assert loaded.ticket_id == ticket_id
        assert loaded.turn_count == 3
        assert loaded.rag_call_count == 2
        assert loaded.last_turn_id == "turn_3"
        assert loaded.status == "active"

    finally:
        cleanup_state(second_db, ticket_id)
        second_db.close()


def test_sql_conversation_state_store_can_persist_closed_status(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationStateStore(db_session)

    state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=2,
        rag_call_count=1,
        last_turn_id="turn_2",
        status="closed",
    )

    try:
        store.save(ticket_id=ticket_id, state=state)

        loaded = store.get(ticket_id)

        assert loaded is not None
        assert loaded.status == "closed"

    finally:
        cleanup_state(db_session, ticket_id)


def test_sql_conversation_state_store_can_persist_escalated_status(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationStateStore(db_session)

    state = make_conversation_state(
        ticket_id=ticket_id,
        turn_count=5,
        rag_call_count=2,
        last_turn_id="turn_5",
        status="escalated",
    )

    try:
        store.save(ticket_id=ticket_id, state=state)

        loaded = store.get(ticket_id)

        assert loaded is not None
        assert loaded.status == "escalated"

    finally:
        cleanup_state(db_session, ticket_id)
