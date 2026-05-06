from __future__ import annotations

import re
from datetime import datetime, timezone

from src.core.conversation_control_models import (
    ConversationControlDecision,
    ConversationControlInput,
)
from src.core.conversation_state_models import ConversationState
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.default_models import (
    PredefinedEscalationResponse,
    PredefinedClosingResponse,
)


class ConversationController:
    """
    Controls objective conversation limits and lightweight conversation status.

    This component does not decide retrieval strategy and does not generate
    responses.

    It only:
    - checks whether RAG is still allowed
    - checks whether escalation must be forced
    - detects pure closing turns
    - updates the operational conversation state after each turn
    """

    def __init__(self, max_turns_per_ticket: int, max_rag_calls_per_ticket: int) -> None:
        if max_turns_per_ticket < 1:
            raise ValueError("max_turns_per_ticket must be greater than 0")

        if max_rag_calls_per_ticket < 0:
            raise ValueError("max_rag_calls_per_ticket cannot be negative")

        self.max_turns_per_ticket = max_turns_per_ticket
        self.max_rag_calls_per_ticket = max_rag_calls_per_ticket

        self.closing_phrases = {
            "thanks",
            "thank you",
            "thanks a lot",
            "thank you very much",
            "many thanks",
            "thx",
            "ty",
            "appreciate it",
            "much appreciated",
            "ok",
            "okay",
            "alright",
            "all right",
            "got it",
            "understood",
            "clear",
            "makes sense",
            "done",
            "fixed",
            "solved",
            "resolved",
            "it works",
            "works now",
            "that works",
            "that worked",
            "that solved it",
            "that fixed it",
            "issue solved",
            "problem solved",
            "everything works",
            "everything is working",
            "no problem",
            "no problems",
            "no more issues",
            "perfect",
            "great",
            "nice",
            "excellent",
            "awesome",
            "cool",
            "good",
            "very good",
            "great thanks",
            "perfect thanks",
            "okay thanks",
            "ok thanks",
            "thanks done",
            "all good",
            "all set",
            "that's all",
            "nothing else",
            "no further questions",
            "bye",
            "goodbye",
            "see you",
            "have a nice day",
            "gracias",
            "muchas gracias",
            "mil gracias",
            "gracias por la ayuda",
            "te lo agradezco",
            "se agradece",
            "muy amable",
            "vale",
            "ok gracias",
            "vale gracias",
            "de acuerdo",
            "entendido",
            "comprendido",
            "claro",
            "perfecto",
            "genial",
            "bien",
            "muy bien",
            "hecho",
            "listo",
            "arreglado",
            "solucionado",
            "resuelto",
            "funciona",
            "ya funciona",
            "ahora funciona",
            "me funciona",
            "funciona bien",
            "todo bien",
            "todo correcto",
            "todo perfecto",
            "todo solucionado",
            "problema resuelto",
            "problema solucionado",
            "incidencia resuelta",
            "incidencia solucionada",
            "sin problema",
            "sin problemas",
            "no tengo más dudas",
            "no tengo mas dudas",
            "nada más",
            "nada mas",
            "eso es todo",
            "adiós",
            "adios",
            "hasta luego",
            "nos vemos",
            "buen día",
            "buen dia",
            "que tengas buen día",
            "que tengas buen dia",
        }

        self.problem_signals = {
            "error",
            "fail",
            "fails",
            "failed",
            "failing",
            "not working",
            "doesn't work",
            "does not work",
            "broken",
            "crash",
            "crashes",
            "drain",
            "drains",
            "overheat",
            "overheats",
            "hot",
            "warm",
            "refund",
            "cancel",
            "warranty",
            "delayed",
            "damaged",
            "can't login",
            "cannot login",
            "not charging",
            "issue",
            "problem",
            "fallo",
            "falla",
            "fallando",
            "no funciona",
            "roto",
            "rota",
            "se bloquea",
            "se calienta",
            "calienta",
            "batería",
            "bateria",
            "descarga",
            "devolver",
            "devolución",
            "devolucion",
            "reembolso",
            "cancelar",
            "garantía",
            "garantia",
            "tarde",
            "retrasado",
            "dañado",
            "dañada",
            "no carga",
            "problema",
        }

    def decide(self, control_input: ConversationControlInput) -> ConversationControlDecision:
        """
        Decide whether the current turn can continue with RAG,
        must be closed, or must be escalated.
        """
        ticket = control_input.ticket
        state = control_input.conversation_state

        description = self._normalize_text(ticket.description)

        if state.status == "closed":
            return ConversationControlDecision(
                allow_rag=False,
                force_escalation=False,
                control_type="closed",
                reason="Conversation is already closed.",
            )

        if state.status == "escalated":
            return ConversationControlDecision(
                allow_rag=False,
                force_escalation=True,
                control_type="escalate",
                reason="Conversation is already escalated.",
            )

        if self._is_closing_turn(description) and not self._has_problem_signal(description):
            return ConversationControlDecision(
                allow_rag=False,
                force_escalation=False,
                control_type="closed",
                reason="The current user turn is a pure closing or acknowledgement message.",
            )

        if state.turn_count >= self.max_turns_per_ticket:
            return ConversationControlDecision(
                allow_rag=False,
                force_escalation=True,
                control_type="escalate",
                reason="Maximum number of turns reached.",
            )

        if state.rag_call_count >= self.max_rag_calls_per_ticket:
            return ConversationControlDecision(
                allow_rag=False,
                force_escalation=False,
                control_type="max_rag_calls_reached",
                reason="Maximum number of RAG calls reached.",
            )

        return ConversationControlDecision(
            allow_rag=True,
            force_escalation=False,
            control_type="active",
            reason="Conversation is active and within allowed limits.",
        )

    def update_state(
        self,
        previous_state: ConversationState,
        ticket: Ticket,
        control_decision: ConversationControlDecision,
        retrieval_decision: RetrievalPolicyDecision | None = None,
        response: ResponseOutput | None = None,
        predefined_closing_response: PredefinedClosingResponse | None = None,
        predefined_escalation_response: PredefinedEscalationResponse | None = None,
    ) -> ConversationState:
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

        now = self._now()

        turn_count = previous_state.turn_count
        rag_call_count = previous_state.rag_call_count
        last_turn_id = previous_state.last_turn_id
        status = previous_state.status

        has_response = response is not None
        has_predefined_closing = predefined_closing_response is not None
        has_predefined_escalation = predefined_escalation_response is not None

        has_only_predefined_closing = (
            has_predefined_closing
            and not has_response
            and not has_predefined_escalation
        )

        has_only_predefined_escalation = (
            has_predefined_escalation
            and not has_response
            and not has_predefined_closing
        )

        if self._is_new_turn(
            current_turn_id=ticket.turn_id,
            last_turn_id=previous_state.last_turn_id,
        ):
            turn_count += 1
            last_turn_id = self._normalize_optional_str(ticket.turn_id)

        if retrieval_decision is not None and retrieval_decision.use_rag:
            rag_call_count += 1

        if control_decision.control_type == "closed":
            status = "closed"

        if has_only_predefined_closing:
            status = "closed"

        if control_decision.force_escalation:
            status = "escalated"

        if has_only_predefined_escalation:
            status = "escalated"

        if response is not None and response.requires_escalation:
            status = "escalated"

        return ConversationState(
            ticket_id=previous_state.ticket_id.strip(),
            turn_count=turn_count,
            rag_call_count=rag_call_count,
            last_turn_id=last_turn_id,
            status=status,
            created_at=previous_state.created_at,
            updated_at=now,
        )

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
    def _normalize_text(text: str | None) -> str:
        if not text:
            return ""

        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _is_closing_turn(self, description: str) -> bool:
        if not description:
            return False

        return description in self.closing_phrases

    def _has_problem_signal(self, description: str) -> bool:
        if not description:
            return False

        return any(signal in description for signal in self.problem_signals)

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
