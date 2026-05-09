from __future__ import annotations

from datetime import datetime

import pytest

from src.conversation.conversation_updater import ConversationUpdater
from src.core.conversation_state_models import ConversationState
from src.core.default_models import (
    PredefinedClosingResponse,
    PredefinedEscalationResponse,
)
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def updater() -> ConversationUpdater:
    return ConversationUpdater()


@pytest.fixture
def ticket() -> Ticket:
    return Ticket(
        ticket_id="ticket_001",
        turn_id="turn_001",
        source="email",
        description="My device battery drains very quickly.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )


@pytest.fixture
def active_state() -> ConversationState:
    return ConversationState(
        ticket_id="ticket_001",
        turn_count=2,
        rag_call_count=1,
        last_turn_id="turn_000",
        status="active",
        created_at="2026-05-05T10:00:00+00:00",
        updated_at="2026-05-05T10:10:00+00:00",
    )


# =============================================================================
# Helpers
# =============================================================================


def make_ticket(
    description: str = "My device battery drains very quickly.",
    ticket_id: str | None = "ticket_001",
    turn_id: str | None = "turn_001",
    source: str | None = "email",
    domain: str = "technical_support",
    subdomain: str = "battery_life",
    product: str = "iphone",
) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        turn_id=turn_id,
        source=source,
        description=description,
        domain=domain,
        subdomain=subdomain,
        product=product,
    )


def make_state(
    ticket_id: str = "ticket_001",
    turn_count: int = 2,
    rag_call_count: int = 1,
    last_turn_id: str | None = "turn_000",
    status: str = "active",
    created_at: str | None = "2026-05-05T10:00:00+00:00",
    updated_at: str | None = "2026-05-05T10:10:00+00:00",
) -> ConversationState:
    return ConversationState(
        ticket_id=ticket_id,
        turn_count=turn_count,
        rag_call_count=rag_call_count,
        last_turn_id=last_turn_id,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
    )


def make_retrieval_decision(
    use_rag: bool,
    retrieval_mode: str = "semantic",
    decision_type: str = "problem_update",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=False,
        is_initial_turn=False,
        retrieval_mode=retrieval_mode,
        decision_type=decision_type,
        reason="Test retrieval decision.",
    )


def make_response(
    requires_escalation: bool = False,
    should_close: bool = False,
    resolution_type: str = "direct_solution",
) -> ResponseOutput:
    return ResponseOutput(
        response="Test response.",
        tone="professional",
        resolution_type=resolution_type,
        requires_escalation=requires_escalation,
        should_close=should_close,
        confidence=0.9,
        escalation_channel="support_ticket" if requires_escalation else "none",
    )


def make_predefined_closing_response() -> PredefinedClosingResponse:
    return PredefinedClosingResponse(
        response="Gracias por confirmarlo. Cierro el caso como resuelto."
    )


def make_predefined_escalation_response() -> PredefinedEscalationResponse:
    return PredefinedEscalationResponse(
        response="Voy a escalar este caso a soporte humano."
    )


# =============================================================================
# update_state tests: response path validation
# =============================================================================


def test_update_state_requires_exactly_one_response_path(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one response path must be provided per update_state call.",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
        )


def test_update_state_rejects_multiple_response_paths_response_and_closing(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one response path must be provided per update_state call.",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            response=make_response(),
            predefined_closing_response=make_predefined_closing_response(),
        )


def test_update_state_rejects_multiple_response_paths_response_and_escalation(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one response path must be provided per update_state call.",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            response=make_response(),
            predefined_escalation_response=make_predefined_escalation_response(),
        )


def test_update_state_rejects_both_predefined_responses(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    with pytest.raises(
        ValueError,
        match="Exactly one response path must be provided per update_state call.",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            predefined_closing_response=make_predefined_closing_response(),
            predefined_escalation_response=make_predefined_escalation_response(),
        )


# =============================================================================
# update_state tests: turn count
# =============================================================================


def test_update_state_increments_turn_count_for_new_turn(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id == "turn_001"


def test_update_state_does_not_increment_turn_count_for_repeated_turn_id(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Same turn retried.",
        turn_id="turn_000",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.turn_count == active_state.turn_count
    assert result.last_turn_id == active_state.last_turn_id


def test_update_state_increments_turn_count_when_ticket_turn_id_is_none(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn without id.",
        turn_id=None,
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id is None


def test_update_state_increments_turn_count_when_ticket_turn_id_is_blank(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn with blank id.",
        turn_id="   ",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id is None


def test_update_state_normalizes_last_turn_id(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn with padded id.",
        turn_id="  turn_001  ",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.last_turn_id == "turn_001"


# =============================================================================
# update_state tests: RAG count
# =============================================================================


def test_update_state_increments_rag_call_count_when_new_turn_uses_rag(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    retrieval_decision = make_retrieval_decision(use_rag=True)

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        retrieval_decision=retrieval_decision,
        response=make_response(),
    )

    assert result.rag_call_count == active_state.rag_call_count + 1


def test_update_state_does_not_increment_rag_call_count_when_retrieval_does_not_use_rag(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        retrieval_mode="none",
        decision_type="insufficient_information",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        retrieval_decision=retrieval_decision,
        response=make_response(),
    )

    assert result.rag_call_count == active_state.rag_call_count


def test_update_state_does_not_increment_rag_call_count_when_retrieval_decision_is_none(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        retrieval_decision=None,
        response=make_response(),
    )

    assert result.rag_call_count == active_state.rag_call_count


def test_update_state_does_not_increment_rag_call_count_for_repeated_turn_id_even_if_use_rag_true(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Same turn retried.",
        turn_id="turn_000",
    )
    retrieval_decision = make_retrieval_decision(use_rag=True)

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        retrieval_decision=retrieval_decision,
        response=make_response(),
    )

    assert result.turn_count == active_state.turn_count
    assert result.rag_call_count == active_state.rag_call_count


# =============================================================================
# update_state tests: status
# =============================================================================


def test_update_state_marks_closed_with_predefined_closing_response(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        predefined_closing_response=make_predefined_closing_response(),
    )

    assert result.status == "closed"


def test_update_state_marks_escalated_with_predefined_escalation_response(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        predefined_escalation_response=make_predefined_escalation_response(),
    )

    assert result.status == "escalated"


def test_update_state_marks_escalated_when_response_requires_escalation(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    response = make_response(
        requires_escalation=True,
        should_close=False,
        resolution_type="escalation",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=response,
    )

    assert result.status == "escalated"


def test_update_state_marks_closed_when_response_should_close(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    response = make_response(
        requires_escalation=False,
        should_close=True,
        resolution_type="direct_solution",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=response,
    )

    assert result.status == "closed"


def test_update_state_marks_active_when_response_does_not_escalate_or_close(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    response = make_response(
        requires_escalation=False,
        should_close=False,
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=response,
    )

    assert result.status == "active"


def test_update_state_can_reopen_closed_state_when_response_is_active(
    updater: ConversationUpdater,
    ticket: Ticket,
) -> None:
    previous_state = make_state(status="closed")

    result = updater.update_state(
        previous_state=previous_state,
        ticket=ticket,
        response=make_response(
            requires_escalation=False,
            should_close=False,
        ),
    )

    assert result.status == "active"


def test_update_state_can_move_escalated_state_to_active_when_response_is_active(
    updater: ConversationUpdater,
    ticket: Ticket,
) -> None:
    previous_state = make_state(status="escalated")

    result = updater.update_state(
        previous_state=previous_state,
        ticket=ticket,
        response=make_response(
            requires_escalation=False,
            should_close=False,
        ),
    )

    assert result.status == "active"


def test_update_state_response_escalation_has_priority_over_should_close_if_both_true(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    response = make_response(
        requires_escalation=True,
        should_close=True,
        resolution_type="escalation",
    )

    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=response,
    )

    assert result.status == "escalated"


# =============================================================================
# update_state tests: timestamps and identity
# =============================================================================


def test_update_state_preserves_created_at(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.created_at == active_state.created_at


def test_update_state_updates_updated_at(
    updater: ConversationUpdater,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = updater.update_state(
        previous_state=active_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.updated_at is not None
    assert result.updated_at != active_state.updated_at

    parsed_updated_at = datetime.fromisoformat(result.updated_at)

    assert parsed_updated_at.tzinfo is not None


def test_update_state_normalizes_ticket_id_in_returned_state(
    updater: ConversationUpdater,
    ticket: Ticket,
) -> None:
    previous_state = make_state(ticket_id="  ticket_001  ")

    result = updater.update_state(
        previous_state=previous_state,
        ticket=ticket,
        response=make_response(),
    )

    assert result.ticket_id == "ticket_001"


def test_update_state_raises_error_when_ticket_id_is_none(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Missing ticket id.",
        ticket_id=None,
    )

    with pytest.raises(
        ValueError,
        match="ticket.ticket_id is required to update conversation state",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            response=make_response(),
        )


def test_update_state_raises_error_when_ticket_id_is_blank(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Blank ticket id.",
        ticket_id="   ",
    )

    with pytest.raises(
        ValueError,
        match="ticket.ticket_id is required to update conversation state",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            response=make_response(),
        )


def test_update_state_raises_error_when_ticket_id_does_not_match_state(
    updater: ConversationUpdater,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Different ticket id.",
        ticket_id="ticket_002",
    )

    with pytest.raises(
        ValueError,
        match="ticket.ticket_id must match previous_state.ticket_id",
    ):
        updater.update_state(
            previous_state=active_state,
            ticket=ticket,
            response=make_response(),
        )


# =============================================================================
# Internal helper tests: turn deduplication
# =============================================================================


def test_is_new_turn_returns_true_when_current_turn_id_is_none() -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id=None,
        last_turn_id="turn_001",
    )

    assert result is True


@pytest.mark.parametrize(
    "blank_turn_id",
    [
        "",
        " ",
        "   ",
        "\n",
        "\t",
    ],
)
def test_is_new_turn_returns_true_when_current_turn_id_is_blank(
    blank_turn_id: str,
) -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id=blank_turn_id,
        last_turn_id="turn_001",
    )

    assert result is True


def test_is_new_turn_returns_true_when_last_turn_id_is_none() -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id="turn_001",
        last_turn_id=None,
    )

    assert result is True


@pytest.mark.parametrize(
    "blank_last_turn_id",
    [
        "",
        " ",
        "   ",
        "\n",
        "\t",
    ],
)
def test_is_new_turn_returns_true_when_last_turn_id_is_blank(
    blank_last_turn_id: str,
) -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id="turn_001",
        last_turn_id=blank_last_turn_id,
    )

    assert result is True


def test_is_new_turn_returns_false_when_turn_ids_match() -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id="turn_001",
        last_turn_id="turn_001",
    )

    assert result is False


def test_is_new_turn_returns_false_when_turn_ids_match_after_stripping() -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id="  turn_001  ",
        last_turn_id="turn_001",
    )

    assert result is False


def test_is_new_turn_returns_true_when_turn_ids_are_different() -> None:
    result = ConversationUpdater._is_new_turn(
        current_turn_id="turn_002",
        last_turn_id="turn_001",
    )

    assert result is True


# =============================================================================
# Internal helper tests: optional string normalization and clock
# =============================================================================


def test_normalize_optional_str_returns_none_for_none() -> None:
    result = ConversationUpdater._normalize_optional_str(None)

    assert result is None


@pytest.mark.parametrize(
    "blank_value",
    [
        "",
        " ",
        "   ",
        "\n",
        "\t",
    ],
)
def test_normalize_optional_str_returns_none_for_blank_string(
    blank_value: str,
) -> None:
    result = ConversationUpdater._normalize_optional_str(blank_value)

    assert result is None


def test_normalize_optional_str_strips_non_blank_string() -> None:
    result = ConversationUpdater._normalize_optional_str("  turn_001  ")

    assert result == "turn_001"


def test_now_returns_iso_datetime_with_timezone() -> None:
    result = ConversationUpdater._now()

    parsed_result = datetime.fromisoformat(result)

    assert parsed_result.tzinfo is not None
