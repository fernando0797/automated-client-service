from __future__ import annotations

from src.core.memory_models import ConversationMemory


class InMemoryConversationStore:
    """
    Temporary in-memory store for conversational memory.

    This store keeps one ConversationMemory per ticket_id.
    It is intended for development and testing before replacing it
    with a persistent SQL-backed store.
    """

    def __init__(self) -> None:
        self._memories: dict[str, ConversationMemory] = {}

    def get(self, ticket_id: str | None) -> ConversationMemory | None:
        """
        Retrieve the conversation memory associated with a ticket_id.

        Returns None when:
        - ticket_id is None
        - ticket_id is blank
        - no memory exists for that ticket_id
        """
        if not ticket_id or not ticket_id.strip():
            return None

        return self._memories.get(ticket_id.strip())

    def save(self, ticket_id: str | None, memory: ConversationMemory) -> None:
        """
        Save or overwrite the conversation memory associated with a ticket_id.

        Raises:
            ValueError: if ticket_id is None or blank.
            ValueError: if memory.memory is blank.
        """
        if not ticket_id or not ticket_id.strip():
            raise ValueError(
                "ticket_id is required to save conversation memory")

        if not memory.memory or not memory.memory.strip():
            raise ValueError("conversation memory cannot be empty")

        self._memories[ticket_id.strip()] = memory

    def delete(self, ticket_id: str | None) -> None:
        """
        Delete the memory associated with a ticket_id, if it exists.
        """
        if not ticket_id or not ticket_id.strip():
            return

        self._memories.pop(ticket_id.strip(), None)

    def exists(self, ticket_id: str | None) -> bool:
        """
        Check whether a valid memory exists for a ticket_id.
        """
        if not ticket_id or not ticket_id.strip():
            return False

        return ticket_id.strip() in self._memories

    def clear(self) -> None:
        """
        Remove all stored memories.

        Useful for tests.
        """
        self._memories.clear()
