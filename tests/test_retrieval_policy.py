from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.core.request_models import Ticket
from src.core.retrieval_policy_models import (
    RetrievalPolicyDecision,
    RetrievalPolicyInput,
)
from src.rag.retrieval_policy import RetrievalPolicy
from src.validation.input_validator import InputValidator


# =============================================================================
# Helpers
# =============================================================================


def make_ticket(
    description: str,
    turn_id: str | None = "001",
    domain: str = "technical_support",
    subdomain: str = "battery_life",
    product: str = "iphone",
    ticket_id: str | None = "ticket-001",
    source: str | None = "test",
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


def make_policy_input(
    description: str,
    turn_id: str | None = "001",
    memory_context: str | None = None,
    domain: str = "technical_support",
    subdomain: str = "battery_life",
    product: str = "iphone",
) -> RetrievalPolicyInput:
    return RetrievalPolicyInput(
        ticket=make_ticket(
            description=description,
            turn_id=turn_id,
            domain=domain,
            subdomain=subdomain,
            product=product,
        ),
        memory_context=memory_context,
    )


def write_json(path: Path, filename: str, data: dict) -> None:
    file_path = path / filename
    file_path.write_text(json.dumps(data), encoding="utf-8")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def policy() -> RetrievalPolicy:
    return RetrievalPolicy()


@pytest.fixture()
def strict_policy() -> RetrievalPolicy:
    return RetrievalPolicy(
        min_rich_description_words=6,
        min_rich_description_chars=40,
    )


@pytest.fixture()
def taxonomies_path(tmp_path: Path) -> Path:
    write_json(
        tmp_path,
        "domain_schema.json",
        {
            "domains": [
                "technical_support",
                "product_support",
                "administrative",
            ]
        },
    )

    write_json(
        tmp_path,
        "product_catalog.json",
        {
            "products": [
                "iphone",
                "macbook_pro",
                "xbox",
                "sony_playstation",
            ]
        },
    )

    write_json(
        tmp_path,
        "subdomain_schema.json",
        {
            "technical_support": [
                "battery_life",
                "charging",
                "software_error",
                "connectivity",
            ],
            "product_support": [
                "product_setup",
                "peripheral_compatibility",
                "warranty",
            ],
            "administrative": [
                "refund_request",
                "order_status",
                "account_management",
            ],
        },
    )

    return tmp_path


@pytest.fixture()
def input_validator(taxonomies_path: Path) -> InputValidator:
    return InputValidator(taxonomies_path=taxonomies_path)


# =============================================================================
# Model tests
# =============================================================================


def test_retrieval_policy_input_accepts_valid_ticket() -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly after the latest update."
    )

    policy_input = RetrievalPolicyInput(
        ticket=ticket,
        memory_context="Previous conversation summary.",
    )

    assert policy_input.ticket == ticket
    assert policy_input.memory_context == "Previous conversation summary."


def test_retrieval_policy_input_accepts_none_memory_context() -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly after the latest update."
    )

    policy_input = RetrievalPolicyInput(
        ticket=ticket,
        memory_context=None,
    )

    assert policy_input.ticket == ticket
    assert policy_input.memory_context is None


def test_policy_decision_accepts_valid_values() -> None:
    decision = RetrievalPolicyDecision(
        use_rag=True,
        use_memory=False,
        is_initial_turn=True,
        retrieval_mode="hybrid",
        decision_type="metadata_and_description",
        reason="Validated metadata and rich description are available.",
    )

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.is_initial_turn is True
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"
    assert decision.reason == "Validated metadata and rich description are available."


def test_policy_decision_accepts_problem_update_decision_type() -> None:
    decision = RetrievalPolicyDecision(
        use_rag=True,
        use_memory=True,
        is_initial_turn=False,
        retrieval_mode="semantic",
        decision_type="problem_update",
        reason="Later turn adds new problem-related information.",
    )

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.is_initial_turn is False
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "problem_update"


def test_policy_decision_rejects_invalid_retrieval_mode() -> None:
    with pytest.raises(ValidationError):
        RetrievalPolicyDecision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="invalid",
            decision_type="metadata_and_description",
            reason="Invalid mode.",
        )


def test_policy_decision_rejects_invalid_decision_type() -> None:
    with pytest.raises(ValidationError):
        RetrievalPolicyDecision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="hybrid",
            decision_type="new_issue",
            reason="Invalid decision type.",
        )


def test_policy_decision_rejects_closing_decision_type() -> None:
    with pytest.raises(ValidationError):
        RetrievalPolicyDecision(
            use_rag=False,
            use_memory=False,
            is_initial_turn=False,
            retrieval_mode="none",
            decision_type="closing",
            reason="Closing is handled by ConversationController.",
        )


def test_policy_decision_rejects_empty_reason() -> None:
    with pytest.raises(ValidationError):
        RetrievalPolicyDecision(
            use_rag=True,
            use_memory=False,
            is_initial_turn=True,
            retrieval_mode="hybrid",
            decision_type="metadata_and_description",
            reason="",
        )


# =============================================================================
# Normalization tests
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
    policy: RetrievalPolicy,
    raw_text: str | None,
    expected: str,
) -> None:
    assert policy._normalize_text(raw_text) == expected


# =============================================================================
# Memory detection tests
# =============================================================================


@pytest.mark.parametrize(
    "memory_context, expected",
    [
        (None, False),
        ("", False),
        ("   ", False),
        ("\n\t", False),
        ("Previous useful context.", True),
        (" Previous useful context. ", True),
    ],
)
def test_has_memory(
    policy: RetrievalPolicy,
    memory_context: str | None,
    expected: bool,
) -> None:
    assert policy._has_memory(memory_context) is expected


# =============================================================================
# Initial turn detection tests
# =============================================================================


@pytest.mark.parametrize(
    "turn_id",
    [
        None,
        "",
        "1",
        "01",
        "001",
        "turn_1",
        "turn_01",
        "turn_001",
        "TURN_001",
        "message_001",
        "conversation_turn_1",
    ],
)
def test_is_initial_turn_true_for_initial_values(
    policy: RetrievalPolicy,
    turn_id: str | None,
) -> None:
    assert policy._is_initial_turn(turn_id) is True


@pytest.mark.parametrize(
    "turn_id",
    [
        "2",
        "02",
        "002",
        "turn_2",
        "turn_002",
        "message_003",
        "conversation_turn_10",
    ],
)
def test_is_initial_turn_false_for_later_values(
    policy: RetrievalPolicy,
    turn_id: str,
) -> None:
    assert policy._is_initial_turn(turn_id) is False


# =============================================================================
# Rich description tests
# =============================================================================


@pytest.mark.parametrize(
    "description",
    [
        "",
        "help",
        "battery",
        "it fails",
        "not working",
    ],
)
def test_poor_description_is_not_rich(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._has_rich_description(normalized) is False


@pytest.mark.parametrize(
    "description",
    [
        "my iphone battery drains quickly after update",
        "the device overheats when charging",
        "package tracking has not changed for several days",
        "quiero devolver el producto porque llegó dañado",
    ],
)
def test_rich_description_is_detected(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._has_rich_description(normalized) is True


def test_rich_description_can_be_true_by_word_count(policy: RetrievalPolicy) -> None:
    description = "one two three four five"
    normalized = policy._normalize_text(description)

    assert len(normalized.split()) >= policy.min_rich_description_words
    assert policy._has_rich_description(normalized) is True


def test_rich_description_can_be_true_by_character_count(policy: RetrievalPolicy) -> None:
    description = "supercalifragilistic technical issue"
    normalized = policy._normalize_text(description)

    assert len(normalized.split()) < policy.min_rich_description_words
    assert len(normalized) >= policy.min_rich_description_chars
    assert policy._has_rich_description(normalized) is True


def test_strict_policy_changes_rich_description_threshold(
    strict_policy: RetrievalPolicy,
) -> None:
    description = "one two three four five"
    normalized = strict_policy._normalize_text(description)

    assert strict_policy._has_rich_description(normalized) is False


# =============================================================================
# Metadata detection tests
# =============================================================================


def test_has_valid_metadata_true_for_real_valid_ticket(policy: RetrievalPolicy) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly after update.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    assert policy._has_valid_metadata(ticket) is True


@pytest.mark.parametrize(
    "domain, subdomain, product",
    [
        ("", "battery_life", "iphone"),
        ("technical_support", "", "iphone"),
        ("technical_support", "battery_life", ""),
        ("", "", "iphone"),
        ("technical_support", "", ""),
        ("", "battery_life", ""),
        ("", "", ""),
    ],
)
def test_has_valid_metadata_false_for_missing_fields_using_fake_ticket(
    policy: RetrievalPolicy,
    domain: str,
    subdomain: str,
    product: str,
) -> None:
    fake_ticket = SimpleNamespace(
        domain=domain,
        subdomain=subdomain,
        product=product,
    )

    assert policy._has_valid_metadata(fake_ticket) is False


def test_has_valid_metadata_does_not_validate_taxonomy_values(
    policy: RetrievalPolicy,
) -> None:
    fake_ticket = SimpleNamespace(
        domain="invalid_domain",
        subdomain="invalid_subdomain",
        product="invalid_product",
    )

    assert policy._has_valid_metadata(fake_ticket) is True


# =============================================================================
# Problem signal tests
# =============================================================================


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
def test_problem_signal_is_detected(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._has_problem_signal(normalized) is True


@pytest.mark.parametrize(
    "description",
    [
        "hello",
        "thanks",
        "can you explain",
        "what next",
        "nice",
        "de acuerdo",
        "i need setup information for another device model",
    ],
)
def test_non_problem_text_does_not_have_problem_signal(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._has_problem_signal(normalized) is False


# =============================================================================
# Clarification turn tests
# =============================================================================


@pytest.mark.parametrize(
    "description",
    [
        "explain it more simply",
        "what do you mean",
        "can you clarify",
        "summarize",
        "step by step",
        "i don't understand",
        "i do not understand",
        "explícamelo",
        "explicamelo",
        "más simple",
        "mas simple",
        "resume",
        "resúmelo",
        "paso a paso",
        "no lo entiendo",
        "puedes aclararlo",
        "puedes detallarlo",
    ],
)
def test_clarification_turn_is_detected(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._is_clarification_turn(normalized) is True


def test_clarification_with_memory_uses_memory_only(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="explain it more simply",
        turn_id="002",
        memory_context="Previous answer about iPhone battery.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "clarification"


def test_clarification_without_memory_uses_no_rag_and_no_memory(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="explain it more simply",
        turn_id="002",
        memory_context=None,
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "clarification"


def test_clarification_has_priority_over_later_semantic_retrieval(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="explain it more simply",
        turn_id="002",
        memory_context="Previous issue about iPhone battery.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "clarification"


# =============================================================================
# Follow-up tests
# =============================================================================


@pytest.mark.parametrize(
    "description",
    [
        "what should i do next",
        "what next",
        "and now",
        "then what",
        "does that also apply",
        "should i restart",
        "i tried that",
        "still happens",
        "still not working",
        "y ahora",
        "ahora qué",
        "ahora que",
        "qué hago ahora",
        "que hago ahora",
        "eso también aplica",
        "eso tambien aplica",
        "entonces lo reinicio",
        "he probado eso",
        "sigue igual",
        "sigue fallando",
    ],
)
def test_follow_up_turn_is_detected(
    policy: RetrievalPolicy,
    description: str,
) -> None:
    normalized = policy._normalize_text(description)

    assert policy._is_follow_up_turn(normalized) is True


def test_later_short_follow_up_without_new_problem_uses_memory_only(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="what next",
        turn_id="002",
        memory_context="Previous issue about iPhone battery drain.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "follow_up"


def test_later_short_follow_up_without_memory_is_follow_up_but_uses_no_memory(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="what next",
        turn_id="002",
        memory_context=None,
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "follow_up"


def test_later_follow_up_with_rich_problem_uses_semantic_problem_update(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="i tried that but now it overheats while charging",
        turn_id="002",
        memory_context="Previous issue about iPhone battery drain.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "problem_update"


def test_later_short_generic_problem_with_memory_uses_memory_only(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="still fails",
        turn_id="002",
        memory_context="Previous issue about iPhone battery drain.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "follow_up"


def test_later_short_generic_problem_without_memory_is_insufficient(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="still fails",
        turn_id="002",
        memory_context=None,
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "insufficient_information"


# =============================================================================
# Initial turn decision tests
# =============================================================================


def test_initial_turn_with_metadata_and_rich_description_uses_hybrid(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after the latest update",
        turn_id="001",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_initial_turn_with_metadata_and_rich_description_uses_memory_if_available(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after the latest update",
        turn_id="001",
        memory_context="Previous conversation context.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_initial_turn_with_metadata_and_poor_description_uses_filter(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="battery",
        turn_id="001",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "filter"
    assert decision.decision_type == "metadata_only"


def test_initial_turn_without_metadata_and_rich_description_uses_semantic(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after the latest update",
        turn_id="001",
        memory_context=None,
        domain="",
        subdomain="",
        product="",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "description_only"


def test_initial_turn_without_metadata_and_poor_description_is_insufficient(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="help",
        turn_id="001",
        memory_context=None,
        domain="",
        subdomain="",
        product="",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "insufficient_information"


def test_missing_turn_id_is_treated_as_initial_turn(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after the latest update",
        turn_id=None,
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_initial_turn_with_empty_turn_id_is_treated_as_initial_turn(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after the latest update",
        turn_id="",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_initial_closing_like_text_is_not_handled_by_retrieval_policy(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="thanks",
        turn_id="001",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.decision_type == "metadata_only"
    assert decision.use_rag is True
    assert decision.retrieval_mode == "filter"


def test_later_closing_like_text_is_insufficient_if_reaches_retrieval_policy(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="thanks",
        turn_id="002",
        memory_context=None,
    )

    decision = policy.decide(policy_input)

    assert decision.decision_type == "insufficient_information"
    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"


def test_later_closing_like_text_with_memory_is_insufficient_but_memory_available(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="gracias",
        turn_id="002",
        memory_context="Previous issue was about iPhone battery drain.",
    )

    decision = policy.decide(policy_input)

    assert decision.decision_type == "insufficient_information"
    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"


# =============================================================================
# Later turn decision tests: stale metadata protection
# =============================================================================


def test_later_turn_with_new_product_in_description_uses_semantic_not_hybrid(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="actually now my macbook is not charging with the usb c adapter",
        turn_id="002",
        memory_context="Previous issue was about iPhone battery drain.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.retrieval_mode != "hybrid"
    assert decision.retrieval_mode != "filter"
    assert decision.decision_type == "problem_update"


def test_later_turn_with_new_product_and_no_memory_still_uses_semantic(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="actually now my macbook is not charging with the usb c adapter",
        turn_id="002",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "problem_update"


def test_later_turn_with_rich_non_problem_description_uses_semantic_description_only(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="i need setup information for another device model",
        turn_id="002",
        memory_context="Previous issue was about iPhone battery.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "description_only"


def test_later_turn_with_poor_description_and_memory_uses_memory_but_no_rag(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="and then",
        turn_id="002",
        memory_context="Previous issue was about iPhone battery.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "insufficient_information"


def test_later_turn_with_poor_description_and_no_memory_uses_nothing(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="and then",
        turn_id="002",
        memory_context=None,
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.use_memory is False
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "insufficient_information"


@pytest.mark.parametrize(
    "turn_id",
    [
        "002",
        "turn_002",
        "message_003",
        "conversation_turn_10",
    ],
)
def test_later_rich_problem_never_uses_filter_or_hybrid(
    policy: RetrievalPolicy,
    turn_id: str,
) -> None:
    policy_input = make_policy_input(
        description="my macbook is not working after the last system update",
        turn_id=turn_id,
        memory_context="Previous issue was about iPhone battery.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.retrieval_mode == "semantic"
    assert decision.retrieval_mode not in {"filter", "hybrid"}
    assert decision.decision_type == "problem_update"


def test_later_problem_update_has_priority_over_stale_metadata(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="now my playstation crashes every time i open a game",
        turn_id="003",
        memory_context="Previous issue was about iPhone battery drain.",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "problem_update"


def test_later_problematic_message_containing_closing_phrase_is_problem_update(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="thanks but it still fails after restarting",
        turn_id="002",
        memory_context="Previous issue was about iPhone battery drain.",
    )

    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.decision_type == "problem_update"


# =============================================================================
# Output consistency invariants
# =============================================================================


@pytest.mark.parametrize(
    "policy_input",
    [
        make_policy_input(
            description="thanks",
            turn_id="002",
            memory_context=None,
        ),
        make_policy_input(
            description="explain it more simply",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="my iphone battery drains quickly after update",
            turn_id="001",
            memory_context=None,
        ),
        make_policy_input(
            description="battery",
            turn_id="001",
            memory_context=None,
        ),
        make_policy_input(
            description="still fails",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="now my macbook is not charging after update",
            turn_id="002",
            memory_context="ctx",
        ),
    ],
)
def test_decide_always_returns_valid_decision(
    policy: RetrievalPolicy,
    policy_input: RetrievalPolicyInput,
) -> None:
    decision = policy.decide(policy_input)

    assert isinstance(decision, RetrievalPolicyDecision)
    assert isinstance(decision.use_rag, bool)
    assert isinstance(decision.use_memory, bool)
    assert decision.retrieval_mode in {"none", "filter", "semantic", "hybrid"}
    assert decision.decision_type in {
        "clarification",
        "follow_up",
        "problem_update",
        "metadata_only",
        "description_only",
        "metadata_and_description",
        "insufficient_information",
    }
    assert isinstance(decision.reason, str)
    assert len(decision.reason.strip()) > 0


@pytest.mark.parametrize(
    "policy_input",
    [
        make_policy_input(
            description="thanks",
            turn_id="002",
            memory_context=None,
        ),
        make_policy_input(
            description="explain it more simply",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="still fails",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="and then",
            turn_id="002",
            memory_context=None,
        ),
    ],
)
def test_when_use_rag_is_false_retrieval_mode_is_none(
    policy: RetrievalPolicy,
    policy_input: RetrievalPolicyInput,
) -> None:
    decision = policy.decide(policy_input)

    assert decision.use_rag is False
    assert decision.retrieval_mode == "none"


@pytest.mark.parametrize(
    "policy_input",
    [
        make_policy_input(
            description="my iphone battery drains quickly after update",
            turn_id="001",
        ),
        make_policy_input(
            description="battery",
            turn_id="001",
        ),
        make_policy_input(
            description="my macbook is not charging after the update",
            turn_id="002",
            memory_context="ctx",
        ),
    ],
)
def test_when_use_rag_is_true_retrieval_mode_is_not_none(
    policy: RetrievalPolicy,
    policy_input: RetrievalPolicyInput,
) -> None:
    decision = policy.decide(policy_input)

    assert decision.use_rag is True
    assert decision.retrieval_mode in {"filter", "semantic", "hybrid"}


def test_later_turns_that_retrieve_always_use_semantic(
    policy: RetrievalPolicy,
) -> None:
    later_inputs = [
        make_policy_input(
            description="my macbook is not charging after the update",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="the playstation crashes when opening games",
            turn_id="003",
            memory_context="ctx",
        ),
        make_policy_input(
            description="i want to cancel the xbox order because it arrived damaged",
            turn_id="004",
            memory_context=None,
        ),
        make_policy_input(
            description="i need setup information for another device model",
            turn_id="005",
            memory_context="ctx",
        ),
    ]

    for policy_input in later_inputs:
        decision = policy.decide(policy_input)

        assert decision.use_rag is True
        assert decision.retrieval_mode == "semantic"


# =============================================================================
# Reason traceability tests
# =============================================================================


def test_reason_mentions_hybrid_for_initial_hybrid_case(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my iphone battery drains very quickly after update",
        turn_id="001",
    )

    decision = policy.decide(policy_input)

    assert "hybrid" in decision.reason.lower()


def test_reason_mentions_semantic_for_later_problem_update(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="my macbook is not charging after the update",
        turn_id="002",
        memory_context="Previous issue about iPhone battery.",
    )

    decision = policy.decide(policy_input)

    assert decision.decision_type == "problem_update"
    assert "semantic" in decision.reason.lower()


def test_reason_mentions_metadata_for_filter_case(
    policy: RetrievalPolicy,
) -> None:
    policy_input = make_policy_input(
        description="battery",
        turn_id="001",
    )

    decision = policy.decide(policy_input)

    assert "metadata" in decision.reason.lower()


def test_reason_is_never_empty_for_all_main_paths(
    policy: RetrievalPolicy,
) -> None:
    policy_inputs = [
        make_policy_input(description="thanks", turn_id="002"),
        make_policy_input(
            description="explain it more simply",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(
            description="my iphone battery drains quickly after update",
            turn_id="001",
        ),
        make_policy_input(description="battery", turn_id="001"),
        make_policy_input(
            description="my macbook is not charging after update",
            turn_id="002",
            memory_context="ctx",
        ),
        make_policy_input(description="and then", turn_id="002"),
    ]

    for policy_input in policy_inputs:
        decision = policy.decide(policy_input)

        assert decision.reason.strip()


# =============================================================================
# Integration tests: InputValidator -> RetrievalPolicy
# =============================================================================


def test_integration_valid_initial_ticket_passes_validator_and_uses_hybrid(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains very quickly after the latest update.",
        turn_id="001",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context=None,
        )
    )

    assert validated_ticket == ticket
    assert decision.use_rag is True
    assert decision.use_memory is False
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_integration_valid_initial_ticket_with_short_description_uses_filter(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="Battery",
        turn_id="001",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context=None,
        )
    )

    assert decision.use_rag is True
    assert decision.retrieval_mode == "filter"
    assert decision.decision_type == "metadata_only"


def test_integration_valid_later_ticket_with_stale_metadata_uses_semantic(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="Actually now my MacBook is not charging with the USB C adapter.",
        turn_id="002",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context="Previous issue was about iPhone battery drain.",
        )
    )

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.retrieval_mode not in {"filter", "hybrid"}
    assert decision.decision_type == "problem_update"


def test_integration_valid_later_closing_like_ticket_is_not_handled_as_closing_by_policy(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="Gracias",
        turn_id="002",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context="Previous issue was about iPhone battery drain.",
        )
    )

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "insufficient_information"


def test_integration_valid_later_clarification_ticket_uses_memory_only(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="Can you explain it more simply?",
        turn_id="002",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context="Previous assistant response about iPhone battery drain.",
        )
    )

    assert decision.use_rag is False
    assert decision.use_memory is True
    assert decision.retrieval_mode == "none"
    assert decision.decision_type == "clarification"


def test_integration_validator_rejects_empty_description_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="   ",
        turn_id="001",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    with pytest.raises(ValueError, match="Invalid description"):
        input_validator.validate(ticket)


def test_integration_validator_rejects_empty_turn_id_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly.",
        turn_id="   ",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    with pytest.raises(ValueError, match="Invalid turn_id"):
        input_validator.validate(ticket)


def test_integration_validator_rejects_invalid_domain_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly.",
        turn_id="001",
        domain="invalid_domain",
        subdomain="battery_life",
        product="iphone",
    )

    with pytest.raises(ValueError, match="Invalid domain"):
        input_validator.validate(ticket)


def test_integration_validator_rejects_invalid_product_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly.",
        turn_id="001",
        domain="technical_support",
        subdomain="battery_life",
        product="invalid_product",
    )

    with pytest.raises(ValueError, match="Invalid product"):
        input_validator.validate(ticket)


def test_integration_validator_rejects_invalid_subdomain_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly.",
        turn_id="001",
        domain="technical_support",
        subdomain="invalid_subdomain",
        product="iphone",
    )

    with pytest.raises(ValueError, match="Invalid subdomain"):
        input_validator.validate(ticket)


def test_integration_validator_rejects_domain_subdomain_inconsistency_before_policy(
    input_validator: InputValidator,
) -> None:
    ticket = make_ticket(
        description="My iPhone battery drains quickly.",
        turn_id="001",
        domain="administrative",
        subdomain="battery_life",
        product="iphone",
    )

    with pytest.raises(ValueError, match="is not valid for domain"):
        input_validator.validate(ticket)


def test_integration_policy_receives_only_validated_ticket(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="The console crashes when opening games after the last update.",
        turn_id="001",
        domain="technical_support",
        subdomain="software_error",
        product="xbox",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context=None,
        )
    )

    assert decision.use_rag is True
    assert decision.retrieval_mode == "hybrid"
    assert decision.decision_type == "metadata_and_description"


def test_integration_later_turn_new_product_does_not_trust_initial_product_metadata(
    input_validator: InputValidator,
    policy: RetrievalPolicy,
) -> None:
    ticket = make_ticket(
        description="Now the PlayStation crashes every time I open a game.",
        turn_id="003",
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )

    validated_ticket = input_validator.validate(ticket)

    decision = policy.decide(
        RetrievalPolicyInput(
            ticket=validated_ticket,
            memory_context="The previous issue was about an iPhone battery problem.",
        )
    )

    assert decision.use_rag is True
    assert decision.use_memory is True
    assert decision.retrieval_mode == "semantic"
    assert decision.retrieval_mode not in {"filter", "hybrid"}
    assert decision.decision_type == "problem_update"
