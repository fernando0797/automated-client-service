from __future__ import annotations

from src.core.memory_models import LoadedMemory
from src.memory.memory_store import InMemoryConversationStore


class MemoryLoader:
    """
    Loads the current conversation memory for a ticket.

    The loader does not create, update, summarize, or interpret memory.
    It only retrieves existing memory from the store and returns it in
    the format expected by the pipeline.
    """

    def __init__(self, store: InMemoryConversationStore) -> None:
        self.store = store

    def load(self, ticket_id: str | None) -> LoadedMemory:
        """
        Load the conversation memory associated with a ticket_id.

        Returns LoadedMemory(has_memory=False, memory=None) when:
        - ticket_id is None
        - ticket_id is blank
        - no memory exists for that ticket_id
        - the stored memory is empty or blank
        """
        if not ticket_id or not ticket_id.strip():
            return LoadedMemory(
                has_memory=False,
                memory=None,
            )

        memory = self.store.get(ticket_id)

        if memory is None:
            return LoadedMemory(
                has_memory=False,
                memory=None,
            )

        if not memory.memory or not memory.memory.strip():
            return LoadedMemory(
                has_memory=False,
                memory=None,
            )

        return LoadedMemory(
            has_memory=True,
            memory=memory,
        )
