import os
import pytest
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.request_models import Ticket
from src.core.summary_models import SummaryOutput
from src.core.response_models import ResponseInput, ResponseOutput
from src.agents.response_agent import ResponseAgent


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def ticket() -> Ticket:
    return Ticket(
        ticket_id="ticket_001",
        turn_id="turn_001",
        source="email",
        description=(
            "My iPhone battery is draining much faster than usual after the latest update."
        ),
        domain="technical_support",
        subdomain="battery_issue",
        product="iphone",
    )


@pytest.fixture
def summary_output() -> SummaryOutput:
    return SummaryOutput(
        problem="The user reports unexpectedly poor iPhone battery performance.",
        context=(
            "The issue may be related to battery health, background activity, "
            "software updates, or charging behavior."
        ),
        intent="The user wants clear troubleshooting steps to improve battery life.",
    )


@pytest.fixture
def response_input(
    ticket: Ticket,
    summary_output: SummaryOutput,
) -> ResponseInput:
    return ResponseInput(
        ticket=ticket,
        summary=summary_output,
        memory_context=None,
    )


@pytest.fixture
def response_input_without_summary(ticket: Ticket) -> ResponseInput:
    return ResponseInput(
        ticket=ticket,
        summary=None,
        memory_context=None,
    )


# ============================================================
# 1. Model tests
# ============================================================

def test_response_output_can_be_created() -> None:
    response = ResponseOutput(
        response=(
            "I'm sorry you're experiencing battery issues. "
            "Please check Battery Health and review background app activity."
        ),
        tone="empathetic",
        resolution_type="troubleshooting_steps",
        requires_escalation=False,
        confidence=0.85,
        escalation_channel="none",
    )

    assert response.response
    assert response.tone == "empathetic"
    assert response.resolution_type == "troubleshooting_steps"
    assert response.requires_escalation is False
    assert response.confidence == 0.85
    assert response.escalation_channel == "none"


def test_response_input_can_be_created(
    ticket: Ticket,
    summary_output: SummaryOutput,
) -> None:
    response_input = ResponseInput(
        ticket=ticket,
        summary=summary_output,
        memory_context=None,
    )

    assert response_input.ticket == ticket
    assert response_input.summary == summary_output
    assert response_input.memory_context is None


def test_response_input_can_be_created_without_summary(ticket: Ticket) -> None:
    response_input = ResponseInput(
        ticket=ticket,
        summary=None,
        memory_context=None,
    )

    assert response_input.ticket == ticket
    assert response_input.summary is None
    assert response_input.memory_context is None


def test_response_input_requires_ticket(summary_output: SummaryOutput) -> None:
    with pytest.raises(ValidationError):
        ResponseInput(
            summary=summary_output,
            memory_context=None,
        )


def test_response_output_requires_required_fields() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="Missing required fields",
        )


def test_response_output_rejects_empty_response() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="",
            tone="professional",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=0.8,
            escalation_channel="none",
        )


def test_response_output_rejects_too_long_response() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="x" * 3001,
            tone="professional",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=0.8,
            escalation_channel="none",
        )


def test_response_output_accepts_max_length_response() -> None:
    response = ResponseOutput(
        response="x" * 3000,
        tone="professional",
        resolution_type="direct_solution",
        requires_escalation=False,
        confidence=0.8,
        escalation_channel="none",
    )

    assert len(response.response) == 3000


def test_response_output_rejects_invalid_tone() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="This is a response.",
            tone="friendly",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=0.8,
            escalation_channel="none",
        )


def test_response_output_rejects_invalid_resolution_type() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="This is a response.",
            tone="professional",
            resolution_type="random_resolution",
            requires_escalation=False,
            confidence=0.8,
            escalation_channel="none",
        )


def test_response_output_rejects_invalid_escalation_channel() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="This is a response.",
            tone="professional",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=0.8,
            escalation_channel="whatsapp",
        )


def test_response_output_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="This is a response.",
            tone="professional",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=1.5,
            escalation_channel="none",
        )


def test_response_output_rejects_confidence_below_zero() -> None:
    with pytest.raises(ValidationError):
        ResponseOutput(
            response="This is a response.",
            tone="professional",
            resolution_type="direct_solution",
            requires_escalation=False,
            confidence=-0.1,
            escalation_channel="none",
        )


def test_response_output_allows_none_confidence() -> None:
    response = ResponseOutput(
        response="This is a response.",
        tone="professional",
        resolution_type="direct_solution",
        requires_escalation=False,
        confidence=None,
        escalation_channel="none",
    )

    assert response.confidence is None


def test_response_output_defaults_escalation_channel_to_none() -> None:
    response = ResponseOutput(
        response="This is a response.",
        tone="professional",
        resolution_type="direct_solution",
        requires_escalation=False,
        confidence=0.8,
    )

    assert response.escalation_channel == "none"


# ============================================================
# 2. Prompt construction tests
# ============================================================

def test_build_messages_returns_system_and_human_messages(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


def test_build_messages_includes_ticket_description(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert response_input.ticket.description in human_message


def test_build_messages_includes_summary_when_present(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "STRUCTURED SUMMARY" in human_message
    assert response_input.summary is not None
    assert response_input.summary.problem in human_message
    assert response_input.summary.context in human_message
    assert response_input.summary.intent in human_message


def test_build_messages_does_not_include_summary_section_when_missing(
    response_input_without_summary: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input_without_summary)

    human_message = messages[1].content

    assert "CURRENT TICKET DESCRIPTION" in human_message
    assert response_input_without_summary.ticket.description in human_message
    assert "STRUCTURED SUMMARY" not in human_message


def test_build_messages_does_not_include_memory_context_when_missing(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" not in human_message
    assert "None" not in human_message


def test_build_messages_does_not_include_memory_context_when_blank(
    ticket: Ticket,
    summary_output: SummaryOutput,
) -> None:
    response_input = ResponseInput(
        ticket=ticket,
        summary=summary_output,
        memory_context="   ",
    )

    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" not in human_message


def test_build_messages_includes_memory_context_when_present(
    ticket: Ticket,
    summary_output: SummaryOutput,
) -> None:
    memory_context = "The user previously tried restarting the iPhone."

    response_input = ResponseInput(
        ticket=ticket,
        summary=summary_output,
        memory_context=memory_context,
    )

    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" in human_message
    assert memory_context in human_message


def test_build_messages_with_summary_and_memory_includes_both(
    ticket: Ticket,
    summary_output: SummaryOutput,
) -> None:
    memory_context = "The user already checked Battery Health and it was normal."

    response_input = ResponseInput(
        ticket=ticket,
        summary=summary_output,
        memory_context=memory_context,
    )

    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "STRUCTURED SUMMARY" in human_message
    assert "MEMORY CONTEXT" in human_message
    assert summary_output.problem in human_message
    assert memory_context in human_message


def test_build_messages_without_summary_can_include_memory(
    ticket: Ticket,
) -> None:
    memory_context = "The user previously reported the issue started after an update."

    response_input = ResponseInput(
        ticket=ticket,
        summary=None,
        memory_context=memory_context,
    )

    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    human_message = messages[1].content

    assert "CURRENT TICKET DESCRIPTION" in human_message
    assert ticket.description in human_message
    assert "STRUCTURED SUMMARY" not in human_message
    assert "MEMORY CONTEXT" in human_message
    assert memory_context in human_message


def test_build_messages_system_prompt_mentions_summary_optional(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    system_message = messages[0].content

    assert "If a structured summary is provided" in system_message
    assert "If no structured summary is provided" in system_message


def test_build_messages_system_prompt_mentions_escalation_rules(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    system_message = messages[0].content

    assert "requires_escalation" in system_message
    assert "escalation_channel" in system_message
    assert '"none"' in system_message


def test_build_messages_system_prompt_mentions_response_length_limit(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    messages = agent._build_messages(response_input)

    system_message = messages[0].content

    assert "under 3000 characters" in system_message


# ============================================================
# 3. Agent behavior tests without real LLM call
# ============================================================

class FakeStructuredLLM:
    def invoke(self, messages):
        return ResponseOutput(
            response=(
                "I'm sorry you're experiencing poor battery performance. "
                "Please start by checking Battery Health, reviewing background "
                "app activity, and making sure your iPhone is fully updated."
            ),
            tone="empathetic",
            resolution_type="troubleshooting_steps",
            requires_escalation=False,
            confidence=0.86,
            escalation_channel="none",
        )


class FakeEscalationStructuredLLM:
    def invoke(self, messages):
        return ResponseOutput(
            response=(
                "This case should be reviewed by a support specialist because "
                "the available information is not enough to resolve it safely."
            ),
            tone="professional",
            resolution_type="escalation",
            requires_escalation=True,
            confidence=0.72,
            escalation_channel="support_ticket",
        )


def test_generate_response_returns_response_output(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    agent.structured_llm = FakeStructuredLLM()

    result = agent.generate_response(response_input)

    assert isinstance(result, ResponseOutput)
    assert result.response
    assert result.tone
    assert result.resolution_type
    assert result.requires_escalation is False
    assert result.escalation_channel == "none"


def test_generate_response_works_without_summary(
    response_input_without_summary: ResponseInput,
) -> None:
    agent = ResponseAgent()
    agent.structured_llm = FakeStructuredLLM()

    result = agent.generate_response(response_input_without_summary)

    assert isinstance(result, ResponseOutput)
    assert result.response
    assert result.requires_escalation is False


def test_generate_response_uses_built_messages(
    response_input: ResponseInput,
    monkeypatch,
) -> None:
    agent = ResponseAgent()
    agent.structured_llm = FakeStructuredLLM()

    called = {"value": False}

    def fake_build_messages(input_data):
        called["value"] = True
        return [
            SystemMessage(content="system"),
            HumanMessage(content="human"),
        ]

    monkeypatch.setattr(agent, "_build_messages", fake_build_messages)

    result = agent.generate_response(response_input)

    assert called["value"] is True
    assert isinstance(result, ResponseOutput)


def test_generate_response_can_return_escalation(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()
    agent.structured_llm = FakeEscalationStructuredLLM()

    result = agent.generate_response(response_input)

    assert isinstance(result, ResponseOutput)
    assert result.requires_escalation is True
    assert result.resolution_type == "escalation"
    assert result.escalation_channel == "support_ticket"


# ============================================================
# 4. Integration test with real LLM call
# ============================================================

@pytest.mark.live_llm
@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY is not set",
)
def test_response_agent_real_llm_call_returns_response_output(
    response_input: ResponseInput,
) -> None:
    agent = ResponseAgent()

    result = agent.generate_response(response_input)

    assert isinstance(result, ResponseOutput)

    assert isinstance(result.response, str)
    assert result.response.strip()
    assert len(result.response) <= 3000

    assert result.tone in [
        "professional",
        "empathetic",
        "technical",
        "apologetic",
    ]

    assert result.resolution_type in [
        "direct_solution",
        "troubleshooting_steps",
        "information_request",
        "escalation",
        "policy_explanation",
    ]

    assert isinstance(result.requires_escalation, bool)

    if result.confidence is not None:
        assert 0.0 <= result.confidence <= 1.0

    assert result.escalation_channel in [
        "phone",
        "email",
        "human_chat",
        "support_ticket",
        "none",
    ]

    if result.requires_escalation is False:
        assert result.escalation_channel == "none"
