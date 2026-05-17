from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    turn_id: str = Field(..., min_length=1)
    source: str | None = "frontend"

    description: str = Field(..., min_length=1)

    domain: str = Field(..., min_length=1)
    subdomain: str = Field(..., min_length=1)
    product: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    ticket_id: str
    turn_id: str

    response: str

    status: Literal["active", "closed", "escalated"]

    requires_escalation: bool
    should_close: bool

    retrieval_used: bool | None = None
    retrieval_mode: str | None = None

    initial_route: str | None = None
    nodes_executed: list[str] = Field(default_factory=list)
