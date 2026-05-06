from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.core.conversation_state_models import ConversationState
from src.core.request_models import Ticket


ConversationControlType = Literal[
    "active",
    "closed",
    "escalate",
    "max_rag_calls_reached",
]


class ConversationControlInput(BaseModel):
    ticket: Ticket
    conversation_state: ConversationState


class ConversationControlDecision(BaseModel):
    allow_rag: bool
    force_escalation: bool
    control_type: ConversationControlType
    reason: str = Field(..., min_length=1)
