from __future__ import annotations

from datetime import datetime

import pytest

from src.core.conversation_state_models import ConversationState
from src.conversation.conversation_state_loader import ConversationStateLoader
from src.conversation.conversation_state_store import InMemoryConversationStateStore


@pytest.fixture
def store() -> InMemoryConversationStateStore:
    return InMemoryConversationStateStore()


@pytest.fixture
def loader(
    store: InMemoryConversationStateStore,
) -> ConversationStateLoader:
    return ConversationStateLoader(store=store)


@pytest.fixture
def existing_state() -> ConversationState:
    return ConversationState(
        ticket_id="ticket_001",
        turn_count=3,
        rag_call_count=2,
        last_turn_id="turn_003",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:15:00+00:00",
    )


def test_load_returns_none_when_ticket_id_is_none(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load(None)

    assert result is None


@pytest.mark.parametrize(
    "blank_ticket_id",
    [
        "",
        " ",
        "   ",
        "\n",
        "\t",
    ],
)
def test_load_returns_none_when_ticket_id_is_blank(
    loader: ConversationStateLoader,
    blank_ticket_id: str,
) -> None:
    result = loader.load(blank_ticket_id)

    assert result is None


def test_load_returns_existing_state_when_state_exists(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
    existing_state: ConversationState,
) -> None:
    store.save("ticket_001", existing_state)

    result = loader.load("ticket_001")

    assert result == existing_state


def test_load_normalizes_ticket_id_when_retrieving_existing_state(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
    existing_state: ConversationState,
) -> None:
    store.save("ticket_001", existing_state)

    result = loader.load("  ticket_001  ")

    assert result == existing_state


def test_load_creates_initial_state_when_no_state_exists(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("ticket_001")

    assert result is not None
    assert result.ticket_id == "ticket_001"
    assert result.turn_count == 0
    assert result.rag_call_count == 0
    assert result.last_turn_id is None
    assert result.status == "active"
    assert result.created_at is not None
    assert result.updated_at is not None


def test_load_creates_initial_state_with_normalized_ticket_id(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("  ticket_001  ")

    assert result is not None
    assert result.ticket_id == "ticket_001"


def test_load_initial_state_created_at_is_iso_datetime(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("ticket_001")

    assert result is not None
    assert result.created_at is not None

    parsed_created_at = datetime.fromisoformat(result.created_at)

    assert parsed_created_at.tzinfo is not None


def test_load_initial_state_updated_at_is_iso_datetime(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("ticket_001")

    assert result is not None
    assert result.updated_at is not None

    parsed_updated_at = datetime.fromisoformat(result.updated_at)

    assert parsed_updated_at.tzinfo is not None


def test_load_initial_state_created_at_and_updated_at_are_equal(
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("ticket_001")

    assert result is not None
    assert result.created_at == result.updated_at


def test_load_does_not_persist_initial_state_automatically(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
) -> None:
    result = loader.load("ticket_001")

    assert result is not None
    assert store.exists("ticket_001") is False


def test_load_returns_new_initial_state_each_time_when_not_persisted(
    loader: ConversationStateLoader,
) -> None:
    first_result = loader.load("ticket_001")
    second_result = loader.load("ticket_001")

    assert first_result is not None
    assert second_result is not None
    assert first_result.ticket_id == second_result.ticket_id
    assert first_result.turn_count == second_result.turn_count
    assert first_result.rag_call_count == second_result.rag_call_count
    assert first_result.status == second_result.status
    assert first_result is not second_result


def test_load_existing_state_does_not_create_new_initial_state(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
    existing_state: ConversationState,
) -> None:
    store.save("ticket_001", existing_state)

    result = loader.load("ticket_001")

    assert result == existing_state
    assert result.created_at == existing_state.created_at
    assert result.updated_at == existing_state.updated_at
    assert result.turn_count == existing_state.turn_count
    assert result.rag_call_count == existing_state.rag_call_count
    assert result.last_turn_id == existing_state.last_turn_id


def test_load_existing_closed_state(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
) -> None:
    closed_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=4,
        rag_call_count=1,
        last_turn_id="turn_004",
        status="closed",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:20:00+00:00",
    )

    store.save("ticket_001", closed_state)

    result = loader.load("ticket_001")

    assert result == closed_state
    assert result.status == "closed"


def test_load_existing_escalated_state(
    store: InMemoryConversationStateStore,
    loader: ConversationStateLoader,
) -> None:
    escalated_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=8,
        rag_call_count=4,
        last_turn_id="turn_008",
        status="escalated",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:40:00+00:00",
    )

    store.save("ticket_001", escalated_state)

    result = loader.load("ticket_001")

    assert result == escalated_state
    assert result.status == "escalated"


def test_loader_uses_store_get(
    monkeypatch: pytest.MonkeyPatch,
    store: InMemoryConversationStateStore,
) -> None:
    called_with: list[str | None] = []

    def fake_get(ticket_id: str | None) -> ConversationState | None:
        called_with.append(ticket_id)
        return None

    monkeypatch.setattr(store, "get", fake_get)

    loader = ConversationStateLoader(store=store)

    loader.load("ticket_001")

    assert called_with == ["ticket_001"]


def test_loader_does_not_call_store_get_when_ticket_id_is_none(
    monkeypatch: pytest.MonkeyPatch,
    store: InMemoryConversationStateStore,
) -> None:
    was_called = False

    def fake_get(ticket_id: str | None) -> ConversationState | None:
        nonlocal was_called
        was_called = True
        return None

    monkeypatch.setattr(store, "get", fake_get)

    loader = ConversationStateLoader(store=store)

    result = loader.load(None)

    assert result is None
    assert was_called is False


@pytest.mark.parametrize(
    "blank_ticket_id",
    [
        "",
        " ",
        "   ",
        "\n",
        "\t",
    ],
)
def test_loader_does_not_call_store_get_when_ticket_id_is_blank(
    monkeypatch: pytest.MonkeyPatch,
    store: InMemoryConversationStateStore,
    blank_ticket_id: str,
) -> None:
    was_called = False

    def fake_get(ticket_id: str | None) -> ConversationState | None:
        nonlocal was_called
        was_called = True
        return None

    monkeypatch.setattr(store, "get", fake_get)

    loader = ConversationStateLoader(store=store)

    result = loader.load(blank_ticket_id)

    assert result is None
    assert was_called is False
