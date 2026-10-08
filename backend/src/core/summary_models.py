from pydantic import BaseModel, Field

from src.core.request_models import Ticket
from src.core.context_models import BuiltContext


class SummaryInput(BaseModel):
    ticket: Ticket
    built_context: BuiltContext
    memory_context: str | None = None


class SummaryOutput(BaseModel):
    problem: str = Field(..., min_length=1, max_length=500)
    context: str = Field(..., min_length=1, max_length=1000)
    intent: str = Field(..., min_length=1, max_length=300)
