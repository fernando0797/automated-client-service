from __future__ import annotations
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from src.core.request_models import Ticket


RetrievalMode = Literal["none", "filter", "semantic", "hybrid"]

RetrievalDecisionType = Literal[
    "closing",
    "clarification",
    "follow_up",
    "problem_update",
    "metadata_only",
    "description_only",
    "metadata_and_description",
    "insufficient_information",
]


class RetrievalPolicyInput(BaseModel):
    ticket: Ticket
    memory_context: str | None = None


class RetrievalPolicyDecision(BaseModel):
    use_rag: bool
    use_memory: bool
    retrieval_mode: RetrievalMode
    decision_type: RetrievalDecisionType
    reason: str = Field(..., min_length=1)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value
