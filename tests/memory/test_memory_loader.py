from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.memory_models import ConversationMemory, LoadedMemory
from src.memory.memory_loader import MemoryLoader
from src.memory.memory_store import InMemoryConversationStore


def make_memory(text: str = "The user has an unresolved iPhone battery issue.") -> ConversationMemory:
    return ConversationMemory(memory=text)


@pytest.fixture
def store() -> InMemoryConversationStore:
    return InMemoryConversationStore()


@pytest.fixture
def loader(store: InMemoryConversationStore) -> MemoryLoader:
    return MemoryLoader(store)


# ---------------------------------------------------------------------
# Unit tests: initialization
# ---------------------------------------------------------------------


def test_loader_stores_store_dependency(store: InMemoryConversationStore):
    loader = MemoryLoader(store)

    assert loader.store is store


# ---------------------------------------------------------------------
# Unit tests: missing or blank ticket_id
# ---------------------------------------------------------------------


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_loader_returns_no_memory_for_missing_or_blank_ticket_id(
    loader: MemoryLoader,
    ticket_id: str | None,
):
    result = loader.load(ticket_id)

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is False
    assert result.memory is None


@pytest.mark.parametrize("ticket_id", [None, "", "   ", "\n", "\t"])
def test_loader_does_not_call_store_for_missing_or_blank_ticket_id(
    ticket_id: str | None,
):
    store = MagicMock()
    loader = MemoryLoader(store)

    result = loader.load(ticket_id)

    assert result.has_memory is False
    assert result.memory is None
    store.get.assert_not_called()


# ---------------------------------------------------------------------
# Unit tests: no memory found
# ---------------------------------------------------------------------


def test_loader_returns_no_memory_when_store_has_no_memory(loader: MemoryLoader):
    result = loader.load("ticket-001")

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is False
    assert result.memory is None


def test_loader_calls_store_get_with_ticket_id():
    store = MagicMock()
    store.get.return_value = None

    loader = MemoryLoader(store)

    result = loader.load("ticket-001")

    assert result.has_memory is False
    assert result.memory is None
    store.get.assert_called_once_with("ticket-001")


def test_loader_passes_ticket_id_to_store_without_stripping():
    store = MagicMock()
    store.get.return_value = None

    loader = MemoryLoader(store)

    result = loader.load(" ticket-001 ")

    assert result.has_memory is False
    assert result.memory is None
    store.get.assert_called_once_with(" ticket-001 ")


# ---------------------------------------------------------------------
# Unit tests: valid memory found
# ---------------------------------------------------------------------


def test_loader_returns_loaded_memory_when_memory_exists(
    store: InMemoryConversationStore,
    loader: MemoryLoader,
):
    memory = make_memory("Stored memory for this ticket.")

    store.save("ticket-001", memory)

    result = loader.load("ticket-001")

    assert isinstance(result, LoadedMemory)
    assert result.has_memory is True
    assert result.memory == memory
    assert result.memory.memory == "Stored memory for this ticket."


def test_loader_returns_same_memory_object_from_store():
    memory = make_memory("Stored memory object.")

    store = MagicMock()
    store.get.return_value = memory

    loader = MemoryLoader(store)

    result = loader.load("ticket-001")

    assert result.has_memory is True
    assert result.memory is memory


def test_loader_loads_memory_with_ticket_id_containing_whitespace_when_store_supports_it(
    store: InMemoryConversationStore,
    loader: MemoryLoader,
):
    memory = make_memory("Stored memory with normalized ticket id.")

    store.save("ticket-001", memory)

    result = loader.load(" ticket-001 ")

    assert result.has_memory is True
    assert result.memory == memory


# ---------------------------------------------------------------------
# Unit tests: blank stored memory
# ---------------------------------------------------------------------


@pytest.mark.parametrize("memory_text", ["", "   ", "\n", "\t"])
def test_loader_returns_no_memory_when_stored_memory_is_blank(memory_text: str):
    """
    This simulates a corrupted or externally inserted blank memory.

    The real ConversationMemory model rejects an empty string and the real
    InMemoryConversationStore prevents saving blank memory, so this test uses
    model_construct to verify that the loader remains defensive.
    """
    store = MagicMock()
    store.get.return_value = ConversationMemory.model_construct(
        memory=memory_text)

    loader = MemoryLoader(store)

    result = loader.load("ticket-001")

    assert result.has_memory is False
    assert result.memory is None
    store.get.assert_called_once_with("ticket-001")


def test_loader_returns_no_memory_when_store_returns_memory_with_none_like_empty_value():
    """
    ConversationMemory normally validates memory as a string, so this is mostly
    a defensive test using a mock-like object.
    """
    fake_memory = MagicMock()
    fake_memory.memory = None

    store = MagicMock()
    store.get.return_value = fake_memory

    loader = MemoryLoader(store)

    result = loader.load("ticket-001")

    assert result.has_memory is False
    assert result.memory is None


# ---------------------------------------------------------------------
# Unit tests: store behavior boundaries
# ---------------------------------------------------------------------


def test_loader_does_not_create_memory_when_none_exists(loader: MemoryLoader):
    result = loader.load("ticket-001")

    assert result.has_memory is False
    assert result.memory is None


def test_loader_does_not_modify_existing_memory(
    store: InMemoryConversationStore,
    loader: MemoryLoader,
):
    memory = make_memory("Original memory.")

    store.save("ticket-001", memory)

    result = loader.load("ticket-001")

    assert result.has_memory is True
    assert result.memory == memory
    assert store.get("ticket-001").memory == "Original memory."


def test_loader_does_not_delete_memory_after_loading(
    store: InMemoryConversationStore,
    loader: MemoryLoader,
):
    memory = make_memory("Memory should remain after load.")

    store.save("ticket-001", memory)

    first_result = loader.load("ticket-001")
    second_result = loader.load("ticket-001")

    assert first_result.has_memory is True
    assert second_result.has_memory is True
    assert first_result.memory == memory
    assert second_result.memory == memory
    assert store.exists("ticket-001") is True


# ---------------------------------------------------------------------
# Integration-style tests: loader + real store
# ---------------------------------------------------------------------


def test_loader_integration_save_then_load_returns_memory():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    memory = make_memory(
        "The user reports an iPhone battery drain issue after an update."
    )

    store.save("ticket-001", memory)

    loaded_memory = loader.load("ticket-001")

    assert loaded_memory.has_memory is True
    assert loaded_memory.memory == memory
    assert loaded_memory.memory.memory == memory.memory


def test_loader_integration_load_before_save_then_after_save():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    before_save = loader.load("ticket-001")

    assert before_save.has_memory is False
    assert before_save.memory is None

    memory = make_memory("Memory created after first turn.")
    store.save("ticket-001", memory)

    after_save = loader.load("ticket-001")

    assert after_save.has_memory is True
    assert after_save.memory == memory


def test_loader_integration_load_after_overwrite_returns_latest_memory():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    initial_memory = make_memory("Initial memory after turn one.")
    updated_memory = make_memory("Updated memory after turn two.")

    store.save("ticket-001", initial_memory)

    first_loaded = loader.load("ticket-001")

    assert first_loaded.has_memory is True
    assert first_loaded.memory == initial_memory

    store.save("ticket-001", updated_memory)

    second_loaded = loader.load("ticket-001")

    assert second_loaded.has_memory is True
    assert second_loaded.memory == updated_memory
    assert second_loaded.memory != initial_memory


def test_loader_integration_multiple_tickets_load_correct_memory():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    iphone_memory = make_memory("The user has an iPhone battery issue.")
    refund_memory = make_memory("The user is asking about a refund.")
    switch_memory = make_memory(
        "The user needs help setting up a Nintendo Switch.")

    store.save("ticket-iphone", iphone_memory)
    store.save("ticket-refund", refund_memory)
    store.save("ticket-switch", switch_memory)

    loaded_iphone = loader.load("ticket-iphone")
    loaded_refund = loader.load("ticket-refund")
    loaded_switch = loader.load("ticket-switch")

    assert loaded_iphone.has_memory is True
    assert loaded_iphone.memory == iphone_memory

    assert loaded_refund.has_memory is True
    assert loaded_refund.memory == refund_memory

    assert loaded_switch.has_memory is True
    assert loaded_switch.memory == switch_memory


def test_loader_integration_returns_no_memory_after_delete():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    memory = make_memory("Memory that will be deleted.")

    store.save("ticket-001", memory)

    before_delete = loader.load("ticket-001")
    assert before_delete.has_memory is True
    assert before_delete.memory == memory

    store.delete("ticket-001")

    after_delete = loader.load("ticket-001")
    assert after_delete.has_memory is False
    assert after_delete.memory is None


def test_loader_integration_returns_no_memory_after_clear():
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    store.save("ticket-001", make_memory("First memory."))
    store.save("ticket-002", make_memory("Second memory."))

    assert loader.load("ticket-001").has_memory is True
    assert loader.load("ticket-002").has_memory is True

    store.clear()

    assert loader.load("ticket-001").has_memory is False
    assert loader.load("ticket-002").has_memory is False


def test_loader_returns_memory_with_max_allowed_length(
    store: InMemoryConversationStore,
    loader: MemoryLoader,
):
    memory = make_memory("x" * 1200)

    store.save("ticket-001", memory)

    result = loader.load("ticket-001")

    assert result.has_memory is True
    assert result.memory == memory
    assert len(result.memory.memory) == 1200


def test_loader_can_return_corrupted_too_long_memory_if_store_returns_it():
    """
    The loader only checks whether memory exists and is not blank.
    Length validation belongs to ConversationMemory creation/storage.
    """
    corrupted_memory = ConversationMemory.model_construct(memory="x" * 1201)

    store = MagicMock()
    store.get.return_value = corrupted_memory

    loader = MemoryLoader(store)

    result = loader.load("ticket-001")

    assert result.has_memory is True
    assert result.memory == corrupted_memory


def test_loader_integration_memory_cycle_for_conversation():
    """
    Simulates the operational memory lifecycle:

    Turn 1:
    - no memory exists
    - memory is saved after the response

    Turn 2:
    - loader retrieves previous memory
    - updated memory overwrites the previous one

    Turn 3:
    - loader retrieves the latest memory
    """
    store = InMemoryConversationStore()
    loader = MemoryLoader(store)

    turn_1_loaded = loader.load("ticket-001")

    assert turn_1_loaded.has_memory is False
    assert turn_1_loaded.memory is None

    memory_after_turn_1 = make_memory(
        "The user reports an iPhone battery issue after an update. "
        "The assistant suggested checking battery health."
    )
    store.save("ticket-001", memory_after_turn_1)

    turn_2_loaded = loader.load("ticket-001")

    assert turn_2_loaded.has_memory is True
    assert turn_2_loaded.memory == memory_after_turn_1

    memory_after_turn_2 = make_memory(
        "The user reports an unresolved iPhone battery issue after an update. "
        "The user checked battery health and it is 87%. "
        "The assistant suggested checking background app activity."
    )
    store.save("ticket-001", memory_after_turn_2)

    turn_3_loaded = loader.load("ticket-001")

    assert turn_3_loaded.has_memory is True
    assert turn_3_loaded.memory == memory_after_turn_2
    assert "87%" in turn_3_loaded.memory.memory
