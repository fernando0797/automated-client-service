from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.core.memory_models import ConversationMemory
from src.memory.memory_store import InMemoryConversationStore


def make_memory(text: str = "The user has an unresolved iPhone battery issue.") -> ConversationMemory:
    return ConversationMemory(memory=text)


@pytest.fixture
def store() -> InMemoryConversationStore:
    return InMemoryConversationStore()


# ---------------------------------------------------------------------
# Unit tests: initial state and get()
# ---------------------------------------------------------------------


def test_store_starts_empty(store: InMemoryConversationStore):
    assert store._memories == {}


def test_get_returns_none_for_unknown_ticket_id(store: InMemoryConversationStore):
    result = store.get("unknown-ticket")

    assert result is None


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_get_returns_none_for_missing_or_blank_ticket_id(
    store: InMemoryConversationStore,
    ticket_id: str | None,
):
    result = store.get(ticket_id)

    assert result is None


def test_get_strips_ticket_id_before_lookup(store: InMemoryConversationStore):
    memory = make_memory("Stored memory for ticket 001.")

    store.save("ticket-001", memory)

    assert store.get(" ticket-001 ") == memory
    assert store.get("\tticket-001\n") == memory


# ---------------------------------------------------------------------
# Unit tests: save()
# ---------------------------------------------------------------------


def test_save_stores_memory_by_ticket_id(store: InMemoryConversationStore):
    memory = make_memory("The user has a battery issue.")

    store.save("ticket-001", memory)

    assert store.get("ticket-001") == memory


def test_save_overwrites_existing_memory_for_same_ticket_id(
    store: InMemoryConversationStore,
):
    first_memory = make_memory("Initial memory.")
    updated_memory = make_memory("Updated memory.")

    store.save("ticket-001", first_memory)
    store.save("ticket-001", updated_memory)

    assert store.get("ticket-001") == updated_memory
    assert store.get("ticket-001") != first_memory


def test_save_keeps_memories_separate_by_ticket_id(
    store: InMemoryConversationStore,
):
    first_memory = make_memory("Memory for first ticket.")
    second_memory = make_memory("Memory for second ticket.")

    store.save("ticket-001", first_memory)
    store.save("ticket-002", second_memory)

    assert store.get("ticket-001") == first_memory
    assert store.get("ticket-002") == second_memory


def test_save_strips_ticket_id_before_storing(store: InMemoryConversationStore):
    memory = make_memory("Memory stored with whitespace around ticket id.")

    store.save(" ticket-001 ", memory)

    assert store.get("ticket-001") == memory
    assert store.get(" ticket-001 ") == memory
    assert "ticket-001" in store._memories
    assert " ticket-001 " not in store._memories


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_save_raises_value_error_for_missing_or_blank_ticket_id(
    store: InMemoryConversationStore,
    ticket_id: str | None,
):
    memory = make_memory()

    with pytest.raises(ValueError, match="ticket_id is required"):
        store.save(ticket_id, memory)


@pytest.mark.parametrize("memory_text", ["", "   ", "\n", "\t"])
def test_save_raises_value_error_for_blank_memory(
    store: InMemoryConversationStore,
    memory_text: str,
):
    memory = ConversationMemory.model_construct(memory=memory_text)

    with pytest.raises(ValueError, match="conversation memory cannot be empty"):
        store.save("ticket-001", memory)


def test_save_accepts_memory_with_max_allowed_length(
    store: InMemoryConversationStore,
):
    memory = make_memory("x" * 1200)

    store.save("ticket-001", memory)

    stored_memory = store.get("ticket-001")

    assert stored_memory == memory
    assert stored_memory is not None
    assert len(stored_memory.memory) == 1200


def test_conversation_memory_rejects_too_long_memory():
    with pytest.raises(ValidationError):
        make_memory("x" * 1201)


def test_conversation_memory_rejects_empty_memory():
    with pytest.raises(ValidationError):
        make_memory("")


def test_save_accepts_memory_with_surrounding_whitespace(
    store: InMemoryConversationStore,
):
    memory = make_memory("   Valid memory with surrounding whitespace.   ")

    store.save("ticket-001", memory)

    stored_memory = store.get("ticket-001")
    assert stored_memory == memory
    assert stored_memory is not None
    assert stored_memory.memory == "   Valid memory with surrounding whitespace.   "


# ---------------------------------------------------------------------
# Unit tests: exists()
# ---------------------------------------------------------------------


def test_exists_returns_false_for_unknown_ticket_id(store: InMemoryConversationStore):
    assert store.exists("unknown-ticket") is False


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_exists_returns_false_for_missing_or_blank_ticket_id(
    store: InMemoryConversationStore,
    ticket_id: str | None,
):
    assert store.exists(ticket_id) is False


def test_exists_returns_true_after_save(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory())

    assert store.exists("ticket-001") is True


def test_exists_strips_ticket_id_before_lookup(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory())

    assert store.exists(" ticket-001 ") is True
    assert store.exists("\tticket-001\n") is True


def test_exists_returns_false_after_delete(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory())

    store.delete("ticket-001")

    assert store.exists("ticket-001") is False


# ---------------------------------------------------------------------
# Unit tests: delete()
# ---------------------------------------------------------------------


def test_delete_removes_existing_memory(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory())

    store.delete("ticket-001")

    assert store.get("ticket-001") is None


def test_delete_unknown_ticket_id_does_not_raise(store: InMemoryConversationStore):
    store.delete("unknown-ticket")

    assert store.get("unknown-ticket") is None


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_delete_missing_or_blank_ticket_id_does_not_raise(
    store: InMemoryConversationStore,
    ticket_id: str | None,
):
    store.delete(ticket_id)

    assert store._memories == {}


def test_delete_strips_ticket_id_before_deleting(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory())

    store.delete(" ticket-001 ")

    assert store.get("ticket-001") is None


def test_delete_only_removes_target_ticket(store: InMemoryConversationStore):
    first_memory = make_memory("Memory for ticket 001.")
    second_memory = make_memory("Memory for ticket 002.")

    store.save("ticket-001", first_memory)
    store.save("ticket-002", second_memory)

    store.delete("ticket-001")

    assert store.get("ticket-001") is None
    assert store.get("ticket-002") == second_memory


# ---------------------------------------------------------------------
# Unit tests: clear()
# ---------------------------------------------------------------------


def test_clear_removes_all_memories(store: InMemoryConversationStore):
    store.save("ticket-001", make_memory("First memory."))
    store.save("ticket-002", make_memory("Second memory."))
    store.save("ticket-003", make_memory("Third memory."))

    store.clear()

    assert store._memories == {}
    assert store.get("ticket-001") is None
    assert store.get("ticket-002") is None
    assert store.get("ticket-003") is None


def test_clear_on_empty_store_does_not_raise(store: InMemoryConversationStore):
    store.clear()

    assert store._memories == {}


# ---------------------------------------------------------------------
# Integration-style tests: realistic memory lifecycle
# ---------------------------------------------------------------------


def test_memory_lifecycle_create_update_load_delete(store: InMemoryConversationStore):
    initial_memory = make_memory(
        "The user reports an iPhone battery drain issue after an update."
    )
    updated_memory = make_memory(
        "The user reports an unresolved iPhone battery drain issue after an update. "
        "The assistant suggested checking battery health."
    )

    assert store.get("ticket-001") is None
    assert store.exists("ticket-001") is False

    store.save("ticket-001", initial_memory)

    assert store.exists("ticket-001") is True
    assert store.get("ticket-001") == initial_memory

    store.save("ticket-001", updated_memory)

    assert store.exists("ticket-001") is True
    assert store.get("ticket-001") == updated_memory

    store.delete("ticket-001")

    assert store.exists("ticket-001") is False
    assert store.get("ticket-001") is None


def test_memory_lifecycle_multiple_tickets_do_not_leak_context(
    store: InMemoryConversationStore,
):
    iphone_memory = make_memory(
        "The user has an unresolved iPhone battery issue."
    )
    refund_memory = make_memory(
        "The user is asking about a refund request."
    )
    switch_memory = make_memory(
        "The user needs help setting up a Nintendo Switch."
    )

    store.save("ticket-iphone", iphone_memory)
    store.save("ticket-refund", refund_memory)
    store.save("ticket-switch", switch_memory)

    assert store.get("ticket-iphone") == iphone_memory
    assert store.get("ticket-refund") == refund_memory
    assert store.get("ticket-switch") == switch_memory

    store.save(
        "ticket-iphone",
        make_memory(
            "The user has an unresolved iPhone battery issue and already checked battery health."
        ),
    )

    assert "iPhone" in store.get("ticket-iphone").memory
    assert "refund" in store.get("ticket-refund").memory
    assert "Nintendo Switch" in store.get("ticket-switch").memory


def test_memory_lifecycle_clear_resets_store_after_multiple_operations(
    store: InMemoryConversationStore,
):
    store.save("ticket-001", make_memory("Initial memory."))
    store.save("ticket-001", make_memory("Updated memory."))
    store.save("ticket-002", make_memory("Second ticket memory."))
    store.delete("ticket-002")

    assert store.exists("ticket-001") is True
    assert store.exists("ticket-002") is False

    store.clear()

    assert store.exists("ticket-001") is False
    assert store.exists("ticket-002") is False
    assert store.get("ticket-001") is None
    assert store.get("ticket-002") is None
