from __future__ import annotations

from pydantic import BaseModel, Field

from src.core.request_models import Ticket
from src.core.conversation_state_models import ConversationState
from src.core.conversation_control_models import ConversationControlDecision
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.context_models import BuiltContext
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput
from src.core.memory_models import ConversationMemory
from src.core.default_models import PredefinedClosingResponse, PredefinedEscalationResponse


class PipelineOutput(BaseModel):
    ticket: Ticket

    previous_conversation_state: ConversationState
    conversation_control_decision: ConversationControlDecision
    conversation_state_after: ConversationState | None = None

    previous_conversation_memory: ConversationMemory | None = None
    retrieval_decision: RetrievalPolicyDecision | None = None

    query_rewriter_output: QueryRewriterOutput | None = None
    retrieval_output: RetrievalToolOutput | None = None
    built_context: BuiltContext | None = None
    summary: SummaryOutput | None = None

    response: ResponseOutput | PredefinedEscalationResponse | PredefinedClosingResponse
    memory_after: ConversationMemory | None = None
