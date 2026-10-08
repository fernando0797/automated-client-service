from __future__ import annotations

from src.core.conversation_state_models import ConversationState


class InMemoryConversationStateStore:
    """
    Temporary in-memory store for conversation state.

    This store keeps one ConversationState per ticket_id.
    It is intended for development and testing before replacing it
    with a persistent SQL-backed store.
    """

    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def get(self, ticket_id: str | None) -> ConversationState | None:
        """
        Retrieve the conversation state associated with a ticket_id.

        Returns None when:
        - ticket_id is None
        - ticket_id is blank
        - no state exists for that ticket_id
        """
        if not ticket_id or not ticket_id.strip():
            return None

        return self._states.get(ticket_id.strip())

    def save(self, ticket_id: str | None, state: ConversationState) -> None:
        """
        Save or overwrite the conversation state associated with a ticket_id.

        Raises:
            ValueError: if ticket_id is None or blank.
            ValueError: if state.ticket_id does not match ticket_id.
        """
        if not ticket_id or not ticket_id.strip():
            raise ValueError(
                "ticket_id is required to save conversation state"
            )

        normalized_ticket_id = ticket_id.strip()

        if state.ticket_id.strip() != normalized_ticket_id:
            raise ValueError(
                "state.ticket_id must match the provided ticket_id"
            )

        self._states[normalized_ticket_id] = state

    def delete(self, ticket_id: str | None) -> None:
        """
        Delete the state associated with a ticket_id, if it exists.
        """
        if not ticket_id or not ticket_id.strip():
            return

        self._states.pop(ticket_id.strip(), None)

    def exists(self, ticket_id: str | None) -> bool:
        """
        Check whether a conversation state exists for a ticket_id.
        """
        if not ticket_id or not ticket_id.strip():
            return False

        return ticket_id.strip() in self._states

    def clear(self) -> None:
        """
        Remove all stored conversation states.

        Useful for tests.
        """
        self._states.clear()
