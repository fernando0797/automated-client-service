from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ConversationStateORM(Base):
    __tablename__ = "conversation_state"

    ticket_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rag_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_turn_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ConversationMemoryORM(Base):
    __tablename__ = "conversation_memory"

    ticket_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    memory: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ConversationTraceORM(Base):
    __tablename__ = "conversation_trace"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    turn_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    input_ticket_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    previous_state_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    state_after_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    previous_memory_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    memory_after_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    retrieval_decision_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    query_rewriter_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    retrieval_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    built_context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    initial_route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nodes_executed: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    use_rag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
