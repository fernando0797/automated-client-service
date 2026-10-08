from __future__ import annotations

from typing import Literal, TypedDict

from src.core.context_models import BuiltContext
from src.core.conversation_state_models import ConversationState
from src.core.default_models import (
    PredefinedClosingResponse,
    PredefinedEscalationResponse,
)
from src.core.memory_models import ConversationMemory, LoadedMemory
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.summary_models import SummaryOutput

InitialRoute = Literal[
    "already_closed",
    "already_escalated",
    "force_escalation",
    "rag_limit_reached",
    "active",
]


class SupportGraphState(TypedDict, total=False):
    ticket: Ticket

    previous_conversation_state: ConversationState
    initial_route: InitialRoute
    conversation_state_after: ConversationState

    previous_conversation_memory: LoadedMemory
    memory_after: ConversationMemory | None

    retrieval_decision: RetrievalPolicyDecision | None
    query_rewriter_output: QueryRewriterOutput | None
    retrieval_output: RetrievalToolOutput | None
    built_context: BuiltContext | None
    summary: SummaryOutput | None

    response: ResponseOutput | PredefinedClosingResponse | PredefinedEscalationResponse

    nodes_executed: list[str]
