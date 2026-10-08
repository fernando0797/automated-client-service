from __future__ import annotations

from datetime import datetime, timezone

from src.core.conversation_state_models import ConversationState
from src.conversation.conversation_state_store import InMemoryConversationStateStore


class ConversationStateLoader:
    """
    Loads the current conversation state for a ticket.

    The loader does not update, interpret, or persist state.
    It retrieves existing state from the store. If no state exists for a valid
    ticket_id, it creates an initial ConversationState in the format expected
    by the pipeline.
    """

    def __init__(self, store: InMemoryConversationStateStore) -> None:
        self.store = store

    def load(self, ticket_id: str | None) -> ConversationState | None:
        """
        Load the conversation state associated with a ticket_id.

        Returns None when:
        - ticket_id is None
        - ticket_id is blank

        Returns an initial ConversationState when:
        - ticket_id is valid
        - no state exists for that ticket_id
        """
        if not ticket_id or not ticket_id.strip():
            return None

        normalized_ticket_id = ticket_id.strip()

        state = self.store.get(normalized_ticket_id)

        if state is not None:
            return state

        now = datetime.now(timezone.utc).isoformat()

        return ConversationState(
            ticket_id=normalized_ticket_id,
            turn_count=0,
            rag_call_count=0,
            last_turn_id=None,
            status="active",
            created_at=now,
            updated_at=now,
        )
