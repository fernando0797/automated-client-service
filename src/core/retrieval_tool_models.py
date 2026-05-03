from pydantic import BaseModel, Field
from typing import Literal

from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.request_models import Ticket
from src.core.models import RetrievalResult


class RetrievalToolInput(BaseModel):
    ticket: Ticket
    decision: RetrievalPolicyDecision
    query: str | None = None
    k: int


class RetrievalToolOutput(BaseModel):
    called: bool
    mode_used: Literal["none", "filter", "semantic", "hybrid"]
    optimized_query: str | None = None
    results: list[RetrievalResult] = Field(default_factory=list)
    total_results: int = 0
