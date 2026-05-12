from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from src.core.pipeline_models import PipelineOutput
from src.persistence.models import ConversationTraceORM


def to_json(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    return value


class SQLTraceStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, pipeline_output: PipelineOutput) -> None:
        retrieval_decision = pipeline_output.retrieval_decision
        use_rag = bool(retrieval_decision.use_rag) if retrieval_decision else False

        row = ConversationTraceORM(
            ticket_id=pipeline_output.ticket.ticket_id,
            turn_id=pipeline_output.ticket.turn_id,
            input_ticket_json=to_json(pipeline_output.ticket),
            previous_state_json=to_json(pipeline_output.previous_conversation_state),
            state_after_json=to_json(pipeline_output.conversation_state_after),
            previous_memory_json=to_json(pipeline_output.previous_conversation_memory),
            memory_after_json=to_json(pipeline_output.memory_after),
            retrieval_decision_json=to_json(pipeline_output.retrieval_decision),
            query_rewriter_output_json=to_json(pipeline_output.query_rewriter_output),
            retrieval_output_json=to_json(pipeline_output.retrieval_output),
            built_context_json=to_json(pipeline_output.built_context),
            summary_json=to_json(pipeline_output.summary),
            response_json=to_json(pipeline_output.response),
            initial_route=getattr(pipeline_output, "initial_route", None),
            nodes_executed=getattr(pipeline_output, "nodes_executed", None),
            use_rag=use_rag,
        )

        self.db.add(row)
        self.db.commit()
