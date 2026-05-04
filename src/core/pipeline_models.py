from __future__ import annotations

from pydantic import BaseModel, Field

from src.core.request_models import Ticket
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.context_models import BuiltContext
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseOutput
from src.core.memory_models import ConversationMemory


class PipelineOutput(BaseModel):
    ticket: Ticket

    memory_before: ConversationMemory | None = None
    retrieval_decision: RetrievalPolicyDecision

    query_rewriter_output: QueryRewriterOutput | None = None
    retrieval_output: RetrievalToolOutput | None = None
    built_context: BuiltContext | None = None
    summary: SummaryOutput | None = None

    response: ResponseOutput
    memory_after: ConversationMemory | None = None
