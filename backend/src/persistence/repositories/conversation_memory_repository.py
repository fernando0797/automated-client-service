from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.memory_models import ConversationMemory, LoadedMemory
from src.persistence.models import ConversationMemoryORM


class SQLConversationMemoryStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def load(self, ticket_id: str | None) -> LoadedMemory:
        if not ticket_id or not ticket_id.strip():
            return LoadedMemory(has_memory=False, memory=None)

        row = self.db.get(ConversationMemoryORM, ticket_id)

        if row is None:
            return LoadedMemory(has_memory=False, memory=None)

        return LoadedMemory(
            has_memory=True,
            memory=ConversationMemory(memory=row.memory),
        )

    def save(self, ticket_id: str, memory: ConversationMemory | None) -> None:
        if memory is None:
            return

        existing = self.db.get(ConversationMemoryORM, ticket_id)

        if existing is None:
            row = ConversationMemoryORM(
                ticket_id=ticket_id,
                memory=memory.memory,
            )
            self.db.add(row)
        else:
            existing.memory = memory.memory

        self.db.commit()
