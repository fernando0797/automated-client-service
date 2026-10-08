from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.core.conversation_state_models import ConversationState
from src.conversation.conversation_state_store import InMemoryConversationStateStore


@pytest.fixture
def store() -> InMemoryConversationStateStore:
    return InMemoryConversationStateStore()


@pytest.fixture
def conversation_state() -> ConversationState:
    return ConversationState(
        ticket_id="ticket_001",
        turn_count=2,
        rag_call_count=1,
        last_turn_id="turn_002",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:05:00+00:00",
    )


def test_get_returns_none_when_ticket_id_is_none(
    store: InMemoryConversationStateStore,
) -> None:
    result = store.get(None)

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
def test_get_returns_none_when_ticket_id_is_blank(
    store: InMemoryConversationStateStore,
    blank_ticket_id: str,
) -> None:
    result = store.get(blank_ticket_id)

    assert result is None


def test_get_returns_none_when_state_does_not_exist(
    store: InMemoryConversationStateStore,
) -> None:
    result = store.get("missing_ticket")

    assert result is None


def test_save_stores_conversation_state(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    result = store.get("ticket_001")

    assert result == conversation_state


def test_save_normalizes_ticket_id_key(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("  ticket_001  ", conversation_state)

    result = store.get("ticket_001")

    assert result == conversation_state


def test_get_normalizes_ticket_id_key(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    result = store.get("  ticket_001  ")

    assert result == conversation_state


def test_save_overwrites_existing_state_for_same_ticket_id(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    updated_state = ConversationState(
        ticket_id="ticket_001",
        turn_count=3,
        rag_call_count=2,
        last_turn_id="turn_003",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )

    store.save("ticket_001", conversation_state)
    store.save("ticket_001", updated_state)

    result = store.get("ticket_001")

    assert result == updated_state
    assert result is not conversation_state


def test_save_with_none_ticket_id_raises_value_error(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    with pytest.raises(
        ValueError,
        match="ticket_id is required to save conversation state",
    ):
        store.save(None, conversation_state)


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
def test_save_with_blank_ticket_id_raises_value_error(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
    blank_ticket_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="ticket_id is required to save conversation state",
    ):
        store.save(blank_ticket_id, conversation_state)


def test_save_raises_value_error_when_state_ticket_id_does_not_match_provided_ticket_id(
    store: InMemoryConversationStateStore,
) -> None:
    state = ConversationState(
        ticket_id="ticket_001",
        turn_count=0,
        rag_call_count=0,
        last_turn_id=None,
        status="active",
        created_at=None,
        updated_at=None,
    )

    with pytest.raises(
        ValueError,
        match="state.ticket_id must match the provided ticket_id",
    ):
        store.save("ticket_002", state)


def test_save_allows_matching_ticket_id_after_stripping_provided_ticket_id(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("  ticket_001  ", conversation_state)

    result = store.get("ticket_001")

    assert result == conversation_state


def test_delete_removes_existing_state(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    store.delete("ticket_001")

    assert store.get("ticket_001") is None


def test_delete_normalizes_ticket_id(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    store.delete("  ticket_001  ")

    assert store.get("ticket_001") is None


def test_delete_does_nothing_when_ticket_id_is_none(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    store.delete(None)

    assert store.get("ticket_001") == conversation_state


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
def test_delete_does_nothing_when_ticket_id_is_blank(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
    blank_ticket_id: str,
) -> None:
    store.save("ticket_001", conversation_state)

    store.delete(blank_ticket_id)

    assert store.get("ticket_001") == conversation_state


def test_delete_does_nothing_when_state_does_not_exist(
    store: InMemoryConversationStateStore,
) -> None:
    store.delete("missing_ticket")

    assert store.get("missing_ticket") is None


def test_exists_returns_false_when_ticket_id_is_none(
    store: InMemoryConversationStateStore,
) -> None:
    assert store.exists(None) is False


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
def test_exists_returns_false_when_ticket_id_is_blank(
    store: InMemoryConversationStateStore,
    blank_ticket_id: str,
) -> None:
    assert store.exists(blank_ticket_id) is False


def test_exists_returns_false_when_state_does_not_exist(
    store: InMemoryConversationStateStore,
) -> None:
    assert store.exists("missing_ticket") is False


def test_exists_returns_true_when_state_exists(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    assert store.exists("ticket_001") is True


def test_exists_normalizes_ticket_id(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    store.save("ticket_001", conversation_state)

    assert store.exists("  ticket_001  ") is True


def test_clear_removes_all_states(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    second_state = ConversationState(
        ticket_id="ticket_002",
        turn_count=1,
        rag_call_count=0,
        last_turn_id="turn_001",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:01:00+00:00",
    )

    store.save("ticket_001", conversation_state)
    store.save("ticket_002", second_state)

    store.clear()

    assert store.get("ticket_001") is None
    assert store.get("ticket_002") is None
    assert store.exists("ticket_001") is False
    assert store.exists("ticket_002") is False


def test_clear_on_empty_store_does_not_raise_error(
    store: InMemoryConversationStateStore,
) -> None:
    store.clear()

    assert store.exists("ticket_001") is False


def test_store_keeps_different_ticket_states_independent(
    store: InMemoryConversationStateStore,
    conversation_state: ConversationState,
) -> None:
    second_state = ConversationState(
        ticket_id="ticket_002",
        turn_count=5,
        rag_call_count=3,
        last_turn_id="turn_005",
        status="escalated",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:20:00+00:00",
    )

    store.save("ticket_001", conversation_state)
    store.save("ticket_002", second_state)

    assert store.get("ticket_001") == conversation_state
    assert store.get("ticket_002") == second_state


def test_saved_state_can_have_closed_status(
    store: InMemoryConversationStateStore,
) -> None:
    state = ConversationState(
        ticket_id="ticket_001",
        turn_count=4,
        rag_call_count=2,
        last_turn_id="turn_004",
        status="closed",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:20:00+00:00",
    )

    store.save("ticket_001", state)

    assert store.get("ticket_001") == state


def test_saved_state_can_have_escalated_status(
    store: InMemoryConversationStateStore,
) -> None:
    state = ConversationState(
        ticket_id="ticket_001",
        turn_count=8,
        rag_call_count=4,
        last_turn_id="turn_008",
        status="escalated",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:40:00+00:00",
    )

    store.save("ticket_001", state)

    assert store.get("ticket_001") == state


def test_invalid_conversation_state_status_is_rejected_before_store_save(
    store: InMemoryConversationStateStore,
) -> None:
    with pytest.raises(ValidationError):
        ConversationState(
            ticket_id="ticket_001",
            turn_count=0,
            rag_call_count=0,
            last_turn_id=None,
            status="invalid_status",
            created_at=None,
            updated_at=None,
        )


def test_invalid_negative_turn_count_is_rejected_before_store_save(
    store: InMemoryConversationStateStore,
) -> None:
    with pytest.raises(ValidationError):
        ConversationState(
            ticket_id="ticket_001",
            turn_count=-1,
            rag_call_count=0,
            last_turn_id=None,
            status="active",
            created_at=None,
            updated_at=None,
        )


def test_invalid_negative_rag_call_count_is_rejected_before_store_save(
    store: InMemoryConversationStateStore,
) -> None:
    with pytest.raises(ValidationError):
        ConversationState(
            ticket_id="ticket_001",
            turn_count=0,
            rag_call_count=-1,
            last_turn_id=None,
            status="active",
            created_at=None,
            updated_at=None,
        )
