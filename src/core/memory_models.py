from __future__ import annotations
from pydantic import BaseModel, Field

from src.core.request_models import Ticket
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput


class MemoryUpdateInput(BaseModel):
    ticket: Ticket
    previous_memory: ConversationMemory | None = None
    summary: SummaryOutput | None = None
    response: ResponseOutput


class ConversationMemory(BaseModel):
    memory: str = Field(..., min_length=1, max_length=1200)


class LoadedMemory(BaseModel):
    has_memory: bool
    memory: ConversationMemory | None
