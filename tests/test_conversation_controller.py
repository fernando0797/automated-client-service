from __future__ import annotations

from datetime import datetime

import pytest

from src.conversation.conversation_controller import ConversationController
from src.core.conversation_control_models import (
    ConversationControlDecision,
    ConversationControlInput,
)
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
def controller() -> ConversationController:
    return ConversationController(
        max_turns_per_ticket=8,
        max_rag_calls_per_ticket=4,
    )


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
    description: str,
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
    requires_escalation: bool,
) -> ResponseOutput:
    return ResponseOutput(
        response="Test response.",
        tone="professional",
        resolution_type="direct_solution",
        requires_escalation=requires_escalation,
        confidence=0.9,
        escalation_channel="support_ticket" if requires_escalation else "none",
    )


def make_control_decision(
    allow_rag: bool = True,
    force_escalation: bool = False,
    control_type: str = "active",
    reason: str = "Test control decision.",
) -> ConversationControlDecision:
    return ConversationControlDecision(
        allow_rag=allow_rag,
        force_escalation=force_escalation,
        control_type=control_type,
        reason=reason,
    )


def make_active_control_decision() -> ConversationControlDecision:
    return make_control_decision(
        allow_rag=True,
        force_escalation=False,
        control_type="active",
        reason="Conversation is active and within allowed limits.",
    )


# =============================================================================
# __init__ tests
# =============================================================================


def test_init_accepts_valid_limits() -> None:
    controller = ConversationController(
        max_turns_per_ticket=8,
        max_rag_calls_per_ticket=4,
    )

    assert controller.max_turns_per_ticket == 8
    assert controller.max_rag_calls_per_ticket == 4


@pytest.mark.parametrize(
    "max_turns_per_ticket",
    [
        0,
        -1,
        -10,
    ],
)
def test_init_rejects_invalid_max_turns(
    max_turns_per_ticket: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="max_turns_per_ticket must be greater than 0",
    ):
        ConversationController(
            max_turns_per_ticket=max_turns_per_ticket,
            max_rag_calls_per_ticket=4,
        )


@pytest.mark.parametrize(
    "max_rag_calls_per_ticket",
    [
        -1,
        -10,
    ],
)
def test_init_rejects_invalid_max_rag_calls(
    max_rag_calls_per_ticket: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="max_rag_calls_per_ticket cannot be negative",
    ):
        ConversationController(
            max_turns_per_ticket=8,
            max_rag_calls_per_ticket=max_rag_calls_per_ticket,
        )


# =============================================================================
# decide tests
# =============================================================================


def test_decide_returns_active_when_state_is_active_and_within_limits(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=active_state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is True
    assert result.force_escalation is False
    assert result.control_type == "active"
    assert result.reason == "Conversation is active and within allowed limits."


def test_decide_returns_closed_when_state_is_already_closed(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(status="closed")

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is False
    assert result.control_type == "closed"
    assert result.reason == "Conversation is already closed."


def test_decide_returns_escalate_when_state_is_already_escalated(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(status="escalated")

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is True
    assert result.control_type == "escalate"
    assert result.reason == "Conversation is already escalated."


@pytest.mark.parametrize(
    "description",
    [
        "thanks",
        "thank you",
        "ok",
        "okay",
        "perfect",
        "great",
        "done",
        "solved",
        "resolved",
        "it works",
        "all good",
        "bye",
        "gracias",
        "muchas gracias",
        "vale",
        "ok gracias",
        "perfecto",
        "genial",
        "de acuerdo",
        "solucionado",
        "resuelto",
        "ya funciona",
        "todo bien",
        "nada más",
        "adiós",
        "  GRACIAS  ",
    ],
)
def test_decide_returns_closed_for_pure_closing_turn(
    controller: ConversationController,
    active_state: ConversationState,
    description: str,
) -> None:
    ticket = make_ticket(description=description)

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=active_state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is False
    assert result.control_type == "closed"
    assert result.reason == (
        "The current user turn is a pure closing or acknowledgement message."
    )


@pytest.mark.parametrize(
    "description",
    [
        "thanks but it still fails",
        "ok but the battery still drains",
        "perfect but now it is not charging",
        "gracias pero sigue fallando",
        "vale pero no funciona",
        "perfecto, pero ahora se calienta",
        "gracias, ahora no carga",
    ],
)
def test_decide_does_not_close_when_closing_text_contains_problem_signal(
    controller: ConversationController,
    active_state: ConversationState,
    description: str,
) -> None:
    ticket = make_ticket(description=description)

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=active_state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "active"
    assert result.allow_rag is True
    assert result.force_escalation is False


def test_decide_returns_escalate_when_max_turns_reached(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=8,
        rag_call_count=1,
        last_turn_id="turn_008",
        status="active",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is True
    assert result.control_type == "escalate"
    assert result.reason == "Maximum number of turns reached."


def test_decide_returns_escalate_when_turn_count_exceeds_max_turns(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=9,
        rag_call_count=1,
        last_turn_id="turn_009",
        status="active",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is True
    assert result.control_type == "escalate"
    assert result.reason == "Maximum number of turns reached."


def test_decide_returns_max_rag_calls_reached_when_rag_limit_reached(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=2,
        rag_call_count=4,
        last_turn_id="turn_002",
        status="active",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is False
    assert result.control_type == "max_rag_calls_reached"
    assert result.reason == "Maximum number of RAG calls reached."


def test_decide_returns_max_rag_calls_reached_when_rag_limit_exceeded(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=2,
        rag_call_count=5,
        last_turn_id="turn_002",
        status="active",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.allow_rag is False
    assert result.force_escalation is False
    assert result.control_type == "max_rag_calls_reached"
    assert result.reason == "Maximum number of RAG calls reached."


def test_decide_prioritizes_closed_status_over_current_closing_turn(
    controller: ConversationController,
) -> None:
    ticket = make_ticket(description="thanks")
    state = make_state(status="closed")

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "closed"
    assert result.reason == "Conversation is already closed."


def test_decide_prioritizes_escalated_status_over_current_closing_turn(
    controller: ConversationController,
) -> None:
    ticket = make_ticket(description="thanks")
    state = make_state(status="escalated")

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "escalate"
    assert result.force_escalation is True
    assert result.reason == "Conversation is already escalated."


def test_decide_prioritizes_closed_status_over_turn_limit(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=8,
        rag_call_count=4,
        status="closed",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "closed"
    assert result.force_escalation is False
    assert result.reason == "Conversation is already closed."


def test_decide_prioritizes_escalated_status_over_turn_limit(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    state = make_state(
        turn_count=8,
        rag_call_count=4,
        status="escalated",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "escalate"
    assert result.force_escalation is True
    assert result.reason == "Conversation is already escalated."


def test_decide_prioritizes_current_closing_turn_over_turn_limit(
    controller: ConversationController,
) -> None:
    ticket = make_ticket(description="gracias")
    state = make_state(
        turn_count=8,
        rag_call_count=4,
        status="active",
    )

    control_input = ConversationControlInput(
        ticket=ticket,
        conversation_state=state,
    )

    result = controller.decide(control_input)

    assert result.control_type == "closed"
    assert result.force_escalation is False
    assert result.reason == (
        "The current user turn is a pure closing or acknowledgement message."
    )


# =============================================================================
# update_state tests: turn count
# =============================================================================


def test_update_state_increments_turn_count_for_new_turn(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id == "turn_001"


def test_update_state_does_not_increment_turn_count_for_repeated_turn_id(
    controller: ConversationController,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Same turn retried.",
        turn_id="turn_000",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.turn_count == active_state.turn_count
    assert result.last_turn_id == active_state.last_turn_id


def test_update_state_increments_turn_count_when_ticket_turn_id_is_none(
    controller: ConversationController,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn without id.",
        turn_id=None,
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id is None


def test_update_state_increments_turn_count_when_ticket_turn_id_is_blank(
    controller: ConversationController,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn with blank id.",
        turn_id="   ",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.turn_count == active_state.turn_count + 1
    assert result.last_turn_id is None


def test_update_state_normalizes_last_turn_id(
    controller: ConversationController,
    active_state: ConversationState,
) -> None:
    ticket = make_ticket(
        description="Turn with padded id.",
        turn_id="  turn_001  ",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.last_turn_id == "turn_001"


# =============================================================================
# update_state tests: RAG count
# =============================================================================


def test_update_state_increments_rag_call_count_when_retrieval_uses_rag(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    retrieval_decision = make_retrieval_decision(use_rag=True)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        retrieval_decision=retrieval_decision,
    )

    assert result.rag_call_count == active_state.rag_call_count + 1


def test_update_state_does_not_increment_rag_call_count_when_retrieval_does_not_use_rag(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    retrieval_decision = make_retrieval_decision(
        use_rag=False,
        retrieval_mode="none",
        decision_type="insufficient_information",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        retrieval_decision=retrieval_decision,
    )

    assert result.rag_call_count == active_state.rag_call_count


def test_update_state_does_not_increment_rag_call_count_when_retrieval_decision_is_none(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        retrieval_decision=None,
    )

    assert result.rag_call_count == active_state.rag_call_count


# =============================================================================
# update_state tests: status
# =============================================================================


def test_update_state_marks_closed_when_control_type_is_closed(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_decision = make_control_decision(
        allow_rag=False,
        force_escalation=False,
        control_type="closed",
        reason="The current user turn is a pure closing or acknowledgement message.",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=control_decision,
    )

    assert result.status == "closed"


def test_update_state_marks_closed_with_only_predefined_closing_response(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_closing_response = PredefinedClosingResponse(
        response="Gracias por confirmarlo. Cierro el caso como resuelto."
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        predefined_closing_response=predefined_closing_response,
    )

    assert result.status == "closed"


def test_update_state_marks_escalated_when_control_decision_forces_escalation(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_decision = make_control_decision(
        allow_rag=False,
        force_escalation=True,
        control_type="escalate",
        reason="Maximum number of turns reached.",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=control_decision,
    )

    assert result.status == "escalated"


def test_update_state_marks_escalated_with_only_predefined_escalation_response(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_escalation_response = PredefinedEscalationResponse(
        response="Voy a escalar este caso a soporte humano."
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        predefined_escalation_response=predefined_escalation_response,
    )

    assert result.status == "escalated"


def test_update_state_marks_escalated_when_response_requires_escalation(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    response = make_response(requires_escalation=True)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        response=response,
    )

    assert result.status == "escalated"


def test_update_state_keeps_active_status_when_no_status_change_signal(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_decision = make_control_decision(
        allow_rag=True,
        force_escalation=False,
        control_type="active",
        reason="Conversation is active and within allowed limits.",
    )
    response = make_response(requires_escalation=False)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=control_decision,
        response=response,
    )

    assert result.status == "active"


def test_update_state_keeps_active_when_predefined_closing_is_not_only_predefined_path(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_closing_response = PredefinedClosingResponse(
        response="Closing response."
    )
    response = make_response(requires_escalation=False)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        response=response,
        predefined_closing_response=predefined_closing_response,
    )

    assert result.status == "active"


def test_update_state_keeps_active_when_predefined_escalation_is_not_only_predefined_path(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_escalation_response = PredefinedEscalationResponse(
        response="Escalation response."
    )
    response = make_response(requires_escalation=False)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        response=response,
        predefined_escalation_response=predefined_escalation_response,
    )

    assert result.status == "active"


def test_update_state_keeps_active_when_both_predefined_responses_are_present(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_closing_response = PredefinedClosingResponse(
        response="Closing response."
    )
    predefined_escalation_response = PredefinedEscalationResponse(
        response="Escalation response."
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        predefined_closing_response=predefined_closing_response,
        predefined_escalation_response=predefined_escalation_response,
    )

    assert result.status == "active"


def test_update_state_keeps_closed_status_when_no_escalation_signal(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    previous_state = make_state(status="closed")

    control_decision = make_control_decision(
        allow_rag=False,
        force_escalation=False,
        control_type="closed",
        reason="Conversation is already closed.",
    )

    result = controller.update_state(
        previous_state=previous_state,
        ticket=ticket,
        control_decision=control_decision,
    )

    assert result.status == "closed"


def test_update_state_escalation_has_priority_over_closed_control_type(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_decision = make_control_decision(
        allow_rag=False,
        force_escalation=True,
        control_type="closed",
        reason="Contrived case for escalation priority.",
    )

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=control_decision,
    )

    assert result.status == "escalated"


def test_update_state_response_escalation_has_priority_over_closed_control_type(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    control_decision = make_control_decision(
        allow_rag=False,
        force_escalation=False,
        control_type="closed",
        reason="The current user turn is a pure closing or acknowledgement message.",
    )
    response = make_response(requires_escalation=True)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=control_decision,
        response=response,
    )

    assert result.status == "escalated"


def test_update_state_response_escalation_has_priority_over_predefined_closing(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    predefined_closing_response = PredefinedClosingResponse(
        response="Closing response."
    )
    response = make_response(requires_escalation=True)

    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
        predefined_closing_response=predefined_closing_response,
        response=response,
    )

    assert result.status == "escalated"


def test_update_state_keeps_escalated_status_when_no_new_signal(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    previous_state = make_state(status="escalated")

    result = controller.update_state(
        previous_state=previous_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.status == "escalated"


# =============================================================================
# update_state tests: timestamps and identity
# =============================================================================


def test_update_state_preserves_created_at(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.created_at == active_state.created_at


def test_update_state_updates_updated_at(
    controller: ConversationController,
    ticket: Ticket,
    active_state: ConversationState,
) -> None:
    result = controller.update_state(
        previous_state=active_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.updated_at is not None
    assert result.updated_at != active_state.updated_at

    parsed_updated_at = datetime.fromisoformat(result.updated_at)

    assert parsed_updated_at.tzinfo is not None


def test_update_state_normalizes_ticket_id_in_returned_state(
    controller: ConversationController,
    ticket: Ticket,
) -> None:
    previous_state = make_state(ticket_id="  ticket_001  ")

    result = controller.update_state(
        previous_state=previous_state,
        ticket=ticket,
        control_decision=make_active_control_decision(),
    )

    assert result.ticket_id == "ticket_001"


def test_update_state_raises_error_when_ticket_id_is_none(
    controller: ConversationController,
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
        controller.update_state(
            previous_state=active_state,
            ticket=ticket,
            control_decision=make_active_control_decision(),
        )


def test_update_state_raises_error_when_ticket_id_is_blank(
    controller: ConversationController,
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
        controller.update_state(
            previous_state=active_state,
            ticket=ticket,
            control_decision=make_active_control_decision(),
        )


def test_update_state_raises_error_when_ticket_id_does_not_match_state(
    controller: ConversationController,
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
        controller.update_state(
            previous_state=active_state,
            ticket=ticket,
            control_decision=make_active_control_decision(),
        )


# =============================================================================
# Internal helper tests: text normalization and signals
# =============================================================================


@pytest.mark.parametrize(
    "raw_text, expected",
    [
        ("Hello", "hello"),
        ("  Hello  ", "hello"),
        ("Hello     world", "hello world"),
        ("Hello\nworld", "hello world"),
        ("Hello\tworld", "hello world"),
        ("Mi BATERÍA se descarga", "mi batería se descarga"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_text(
    controller: ConversationController,
    raw_text: str | None,
    expected: str,
) -> None:
    assert controller._normalize_text(raw_text) == expected


@pytest.mark.parametrize(
    "description",
    [
        "thanks",
        "thank you",
        "ok",
        "perfect",
        "gracias",
        "perfecto",
        "ya funciona",
        "nada más",
    ],
)
def test_is_closing_turn_returns_true_for_exact_closing_phrases(
    controller: ConversationController,
    description: str,
) -> None:
    normalized = controller._normalize_text(description)

    assert controller._is_closing_turn(normalized) is True


@pytest.mark.parametrize(
    "description",
    [
        "",
        "thanks but it still fails",
        "gracias pero sigue fallando",
        "hello",
        "i need help",
        "battery problem",
    ],
)
def test_is_closing_turn_returns_false_for_non_exact_closing_phrases(
    controller: ConversationController,
    description: str,
) -> None:
    normalized = controller._normalize_text(description)

    assert controller._is_closing_turn(normalized) is False


@pytest.mark.parametrize(
    "description",
    [
        "error",
        "it fails",
        "not working",
        "doesn't work",
        "broken",
        "crashes",
        "battery drains",
        "overheats",
        "refund",
        "cancel",
        "warranty",
        "delayed package",
        "damaged product",
        "can't login",
        "not charging",
        "issue",
        "problem",
        "fallo",
        "no funciona",
        "roto",
        "se bloquea",
        "se calienta",
        "batería",
        "descarga",
        "devolver",
        "devolución",
        "reembolso",
        "garantía",
        "no carga",
        "problema",
    ],
)
def test_has_problem_signal_returns_true(
    controller: ConversationController,
    description: str,
) -> None:
    normalized = controller._normalize_text(description)

    assert controller._has_problem_signal(normalized) is True


@pytest.mark.parametrize(
    "description",
    [
        "",
        "hello",
        "thanks",
        "gracias",
        "perfect",
        "de acuerdo",
        "what next",
    ],
)
def test_has_problem_signal_returns_false(
    controller: ConversationController,
    description: str,
) -> None:
    normalized = controller._normalize_text(description)

    assert controller._has_problem_signal(normalized) is False


# =============================================================================
# Internal helper tests: turn deduplication
# =============================================================================


def test_is_new_turn_returns_true_when_current_turn_id_is_none() -> None:
    result = ConversationController._is_new_turn(
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
    result = ConversationController._is_new_turn(
        current_turn_id=blank_turn_id,
        last_turn_id="turn_001",
    )

    assert result is True


def test_is_new_turn_returns_true_when_last_turn_id_is_none() -> None:
    result = ConversationController._is_new_turn(
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
    result = ConversationController._is_new_turn(
        current_turn_id="turn_001",
        last_turn_id=blank_last_turn_id,
    )

    assert result is True


def test_is_new_turn_returns_false_when_turn_ids_match() -> None:
    result = ConversationController._is_new_turn(
        current_turn_id="turn_001",
        last_turn_id="turn_001",
    )

    assert result is False


def test_is_new_turn_returns_false_when_turn_ids_match_after_stripping() -> None:
    result = ConversationController._is_new_turn(
        current_turn_id="  turn_001  ",
        last_turn_id="turn_001",
    )

    assert result is False


def test_is_new_turn_returns_true_when_turn_ids_are_different() -> None:
    result = ConversationController._is_new_turn(
        current_turn_id="turn_002",
        last_turn_id="turn_001",
    )

    assert result is True


# =============================================================================
# Internal helper tests: optional string normalization and clock
# =============================================================================


def test_normalize_optional_str_returns_none_for_none() -> None:
    result = ConversationController._normalize_optional_str(None)

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
    result = ConversationController._normalize_optional_str(blank_value)

    assert result is None


def test_normalize_optional_str_strips_non_blank_string() -> None:
    result = ConversationController._normalize_optional_str("  turn_001  ")

    assert result == "turn_001"


def test_now_returns_iso_datetime_with_timezone() -> None:
    result = ConversationController._now()

    parsed_result = datetime.fromisoformat(result)

    assert parsed_result.tzinfo is not None
