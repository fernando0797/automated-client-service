import pytest

from src.core.request_models import Ticket
from src.validation.input_validator import InputValidator


@pytest.fixture(scope="module")
def validator():
    return InputValidator("knowledge/taxonomies")


@pytest.fixture
def valid_ticket():
    return Ticket(
        description="I need help setting up my Amazon Echo.",
        ticket_id="2",
        turn_id="turn_001",
        source="database",
        domain="product_support",
        subdomain="product_setup",
        product="amazon_echo",
    )


def test_validate_returns_ticket_when_input_is_valid(validator, valid_ticket):
    result = validator.validate(valid_ticket)
    assert result == valid_ticket


def test_validate_raises_error_for_invalid_domain(validator, valid_ticket):
    invalid_ticket = valid_ticket.model_copy(
        update={"domain": "product support"})

    with pytest.raises(ValueError, match="Invalid domain"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_invalid_subdomain(validator, valid_ticket):
    invalid_ticket = valid_ticket.model_copy(
        update={"subdomain": "setup_problem"})

    with pytest.raises(ValueError, match="Invalid subdomain"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_invalid_product(validator, valid_ticket):
    invalid_ticket = valid_ticket.model_copy(update={"product": "echo_amazon"})

    with pytest.raises(ValueError, match="Invalid product"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_inconsistent_domain_and_subdomain(
    validator,
    valid_ticket,
):
    invalid_ticket = valid_ticket.model_copy(
        update={
            "domain": "technical_support",
            "subdomain": "product_setup",
        }
    )

    with pytest.raises(ValueError, match="is not valid for domain"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_empty_description(validator, valid_ticket):
    invalid_ticket = valid_ticket.model_copy(update={"description": "   "})

    with pytest.raises(ValueError, match="Invalid description"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_empty_ticket_id_when_present(
    validator,
    valid_ticket,
):
    invalid_ticket = valid_ticket.model_copy(update={"ticket_id": "   "})

    with pytest.raises(ValueError, match="Invalid ticket_id"):
        validator.validate(invalid_ticket)


def test_validate_raises_error_for_empty_turn_id_when_present(
    validator,
    valid_ticket,
):
    invalid_ticket = valid_ticket.model_copy(update={"turn_id": "   "})

    with pytest.raises(ValueError, match="Invalid turn_id"):
        validator.validate(invalid_ticket)


def test_validate_accepts_ticket_without_optional_ids(validator, valid_ticket):
    ticket = valid_ticket.model_copy(
        update={
            "ticket_id": None,
            "turn_id": None,
        }
    )

    result = validator.validate(ticket)

    assert result == ticket
