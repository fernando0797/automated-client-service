from pydantic import BaseModel, Field
from typing import Literal


class ConversationState(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    turn_count: int = Field(default=0, ge=0)
    rag_call_count: int = Field(default=0, ge=0)
    last_turn_id: str | None = None
    status: Literal["active", "closed", "escalated"] = "active"
    created_at: str | None = None
    updated_at: str | None = None
