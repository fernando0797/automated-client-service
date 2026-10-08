from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.conversation_state_models import ConversationState
from src.persistence.models import ConversationStateORM


class SQLConversationStateStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, ticket_id: str | None) -> ConversationState | None:
        if not ticket_id or not ticket_id.strip():
            return None

        row = self.db.get(ConversationStateORM, ticket_id)

        if row is None:
            return None

        return ConversationState(
            ticket_id=row.ticket_id,
            turn_count=row.turn_count,
            rag_call_count=row.rag_call_count,
            last_turn_id=row.last_turn_id,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    def save(self, ticket_id: str, state: ConversationState) -> None:
        existing = self.db.get(ConversationStateORM, ticket_id)

        if existing is None:
            row = ConversationStateORM(
                ticket_id=state.ticket_id,
                turn_count=state.turn_count,
                rag_call_count=state.rag_call_count,
                last_turn_id=state.last_turn_id,
                status=state.status,
            )
            self.db.add(row)
        else:
            existing.turn_count = state.turn_count
            existing.rag_call_count = state.rag_call_count
            existing.last_turn_id = state.last_turn_id
            existing.status = state.status

        self.db.commit()
