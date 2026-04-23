from pydantic import BaseModel

from src.core.request_models import Ticket
from src.core.context_models import BuiltContext


class SummaryInput(BaseModel):
    ticket: Ticket
    built_context: BuiltContext
    memory_context: str | None = None


class SummaryOutput(BaseModel):
    problem: str
    context: str
    intent: str
