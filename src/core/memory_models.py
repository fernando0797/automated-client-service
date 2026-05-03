from __future__ import annotations
from pydantic import BaseModel

from src.core.request_models import Ticket
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput
from src.core.retrieval_tool_models import RetrievalToolOutput


class MemoryUpdateInput(BaseModel):
    ticket: Ticket
    previous_memory: ConversationMemory | None
    summary: SummaryOutput
    response: ResponseOutput


class ConversationMemory(BaseModel):
    memory: str


class LoadedMemory(BaseModel):
    has_memory: bool
    memory: ConversationMemory | None
