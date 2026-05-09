from __future__ import annotations

from datetime import datetime, timezone

from src.core.conversation_state_models import ConversationState
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.default_models import (
    PredefinedEscalationResponse,
    PredefinedClosingResponse,
)


class ConversationUpdater:
    """
    Updates the operational conversation state after each pipeline turn.

    This component does not:
    - decide retrieval strategy
    - interpret user intent
    - generate responses
    - decide whether to use RAG

    It only:
    - validates that the ticket belongs to the current conversation state
    - increments turn_count safely
    - increments rag_call_count when RAG was used
    - updates status from predefined responses or ResponseAgent output
    """

    def update_state(
            self,
            previous_state: ConversationState,
            ticket: Ticket,
            retrieval_decision: RetrievalPolicyDecision | None = None,
            response: ResponseOutput | None = None,
            predefined_closing_response: PredefinedClosingResponse | None = None,
            predefined_escalation_response: PredefinedEscalationResponse | None = None) -> ConversationState:
        """
        Update the conversation state after a pipeline turn.

        The state can be updated from three response paths:
        - normal ResponseAgent path through ResponseOutput
        - predefined closing response path
        - predefined escalation response path
        """
        self._validate_ticket_matches_state(
            ticket=ticket,
            state=previous_state,
        )

        response_paths_count = sum([response is not None,
                                    predefined_closing_response is not None,
                                    predefined_escalation_response is not None])

        if response_paths_count != 1:
            raise ValueError("Exactly one response path must be provided per update_state call.")

        now = self._now()

        turn_count = previous_state.turn_count
        rag_call_count = previous_state.rag_call_count
        last_turn_id = previous_state.last_turn_id
        status = previous_state.status

        is_new_turn = self._is_new_turn(
            current_turn_id=ticket.turn_id,
            last_turn_id=previous_state.last_turn_id)

        if is_new_turn:
            turn_count += 1
            last_turn_id = self._normalize_optional_str(ticket.turn_id)

        if is_new_turn and retrieval_decision is not None and retrieval_decision.use_rag:
            rag_call_count += 1

        if predefined_closing_response is not None:
            status = "closed"

        elif predefined_escalation_response is not None:
            status = "escalated"

        elif response is not None:
            if response.requires_escalation:
                status = "escalated"
            elif response.should_close:
                status = "closed"
            else:
                status = "active"

        return ConversationState(
            ticket_id=previous_state.ticket_id.strip(),
            turn_count=turn_count,
            rag_call_count=rag_call_count,
            last_turn_id=last_turn_id,
            status=status,
            created_at=previous_state.created_at,
            updated_at=now)

    @staticmethod
    def _validate_ticket_matches_state(
        ticket: Ticket,
        state: ConversationState,
    ) -> None:
        """
        Ensure that the incoming ticket belongs to the same conversation state.
        """
        if not ticket.ticket_id or not ticket.ticket_id.strip():
            raise ValueError(
                "ticket.ticket_id is required to update conversation state"
            )

        normalized_ticket_id = ticket.ticket_id.strip()
        normalized_state_ticket_id = state.ticket_id.strip()

        if normalized_ticket_id != normalized_state_ticket_id:
            raise ValueError(
                "ticket.ticket_id must match previous_state.ticket_id"
            )

    @staticmethod
    def _is_new_turn(
        current_turn_id: str | None,
        last_turn_id: str | None,
    ) -> bool:
        """
        Return True when the current turn should be counted.

        If turn_id is missing, the turn is counted because it cannot be
        deduplicated safely.
        """
        if current_turn_id is None or not current_turn_id.strip():
            return True

        if last_turn_id is None or not last_turn_id.strip():
            return True

        return current_turn_id.strip() != last_turn_id.strip()

    @staticmethod
    def _normalize_optional_str(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
