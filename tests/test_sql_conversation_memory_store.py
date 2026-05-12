from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.core.memory_models import ConversationMemory, LoadedMemory
from src.persistence.database import create_db_session
from src.persistence.models import ConversationMemoryORM
from src.persistence.repositories.conversation_memory_repository import (
    SQLConversationMemoryStore,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def unique_ticket_id() -> str:
    return f"test_ticket_{uuid4().hex}"


def make_memory(
    memory_text: str = "The user reported that the phone overheats while charging.",
) -> ConversationMemory:
    return ConversationMemory(memory=memory_text)


@pytest.fixture
def db_session() -> Session:
    db = create_db_session()

    try:
        yield db
    finally:
        db.close()


def cleanup_memory(db: Session, ticket_id: str) -> None:
    row = db.get(ConversationMemoryORM, ticket_id)

    if row is not None:
        db.delete(row)
        db.commit()


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def test_sql_conversation_memory_store_load_returns_empty_when_ticket_id_is_none(
    db_session: Session,
):
    store = SQLConversationMemoryStore(db_session)

    result = store.load(None)

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is False
    assert result.memory is None


def test_sql_conversation_memory_store_load_returns_empty_when_ticket_id_is_empty(
    db_session: Session,
):
    store = SQLConversationMemoryStore(db_session)

    result = store.load("   ")

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is False
    assert result.memory is None


def test_sql_conversation_memory_store_load_returns_empty_when_memory_does_not_exist(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationMemoryStore(db_session)

    result = store.load(ticket_id)

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is False
    assert result.memory is None


def test_sql_conversation_memory_store_save_creates_new_memory(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationMemoryStore(db_session)

    memory = make_memory(
        "The user reported overheating after charging the smartphone."
    )

    try:
        store.save(ticket_id=ticket_id, memory=memory)

        loaded = store.load(ticket_id)

        assert loaded.has_memory is True
        assert loaded.memory is not None
        assert loaded.memory.memory == (
            "The user reported overheating after charging the smartphone."
        )

    finally:
        cleanup_memory(db_session, ticket_id)


def test_sql_conversation_memory_store_save_updates_existing_memory(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationMemoryStore(db_session)

    initial_memory = make_memory(
        "The user reported that the phone overheats."
    )
    updated_memory = make_memory(
        "The user reported that the phone still overheats after changing charger."
    )

    try:
        store.save(ticket_id=ticket_id, memory=initial_memory)
        store.save(ticket_id=ticket_id, memory=updated_memory)

        loaded = store.load(ticket_id)

        assert loaded.has_memory is True
        assert loaded.memory is not None
        assert loaded.memory.memory == (
            "The user reported that the phone still overheats after changing charger."
        )

    finally:
        cleanup_memory(db_session, ticket_id)


def test_sql_conversation_memory_store_save_ignores_none_memory(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationMemoryStore(db_session)

    try:
        store.save(ticket_id=ticket_id, memory=None)

        loaded = store.load(ticket_id)

        assert loaded.has_memory is False
        assert loaded.memory is None

    finally:
        cleanup_memory(db_session, ticket_id)


def test_sql_conversation_memory_store_persists_between_sessions():
    ticket_id = unique_ticket_id()

    first_db = create_db_session()
    try:
        first_store = SQLConversationMemoryStore(first_db)

        memory = make_memory(
            "The user previously tried changing the charger, but overheating continued."
        )

        first_store.save(ticket_id=ticket_id, memory=memory)

    finally:
        first_db.close()

    second_db = create_db_session()
    try:
        second_store = SQLConversationMemoryStore(second_db)

        loaded = second_store.load(ticket_id)

        assert loaded.has_memory is True
        assert loaded.memory is not None
        assert loaded.memory.memory == (
            "The user previously tried changing the charger, but overheating continued."
        )

    finally:
        cleanup_memory(second_db, ticket_id)
        second_db.close()


def test_sql_conversation_memory_store_overwrites_memory_instead_of_creating_duplicates(
    db_session: Session,
):
    ticket_id = unique_ticket_id()
    store = SQLConversationMemoryStore(db_session)

    initial_memory = make_memory("Initial memory.")
    updated_memory = make_memory("Updated memory.")

    try:
        store.save(ticket_id=ticket_id, memory=initial_memory)
        store.save(ticket_id=ticket_id, memory=updated_memory)

        rows = (
            db_session.query(ConversationMemoryORM)
            .filter(ConversationMemoryORM.ticket_id == ticket_id)
            .all()
        )

        assert len(rows) == 1
        assert rows[0].memory == "Updated memory."

    finally:
        cleanup_memory(db_session, ticket_id)
