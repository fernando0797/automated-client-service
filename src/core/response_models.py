from pydantic import BaseModel, Field
from typing import Literal

from src.core.summary_models import SummaryOutput
from src.core.request_models import Ticket


class ResponseInput(BaseModel):
    ticket: Ticket
    summary: SummaryOutput | None = None
    memory_context: str | None = None


class ResponseOutput(BaseModel):
    response: str = Field(..., min_length=1, max_length=3000)
    tone: Literal[
        "professional",
        "empathetic",
        "technical",
        "apologetic",
    ]
    resolution_type: Literal[
        "direct_solution",
        "troubleshooting_steps",
        "information_request",
        "escalation",
        "policy_explanation",
    ]
    requires_escalation: bool
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    escalation_channel: Literal[
        "phone",
        "email",
        "human_chat",
        "support_ticket",
        "none",
    ] = "none"
