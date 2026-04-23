import os
import pytest
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.request_models import Ticket
from src.core.context_models import BuiltContext
from src.core.summary_models import SummaryInput, SummaryOutput
from src.agents.summary_agent import SummaryAgent


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def ticket() -> Ticket:
    return Ticket(
        ticket_id="test_001",
        source="manual_test",
        description=(
            "My iPhone is showing unexpectedly poor battery performance. "
            "The battery does not last as long as it previously did."
        ),
        domain="technical_support",
        subdomain="battery_life",
        product="iphone",
    )


@pytest.fixture
def built_context() -> BuiltContext:
    context_text = (
        "Battery drain issues may be related to background activity, "
        "battery health degradation, software updates, or charging behavior."
    )

    return BuiltContext(
        context_text=context_text,
        results_used=[],
        total_chars=len(context_text),
    )


@pytest.fixture
def summary_input(ticket: Ticket, built_context: BuiltContext) -> SummaryInput:
    return SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context=None,
    )


# ============================================================
# 1. Model tests
# ============================================================

def test_summary_output_can_be_created() -> None:
    summary = SummaryOutput(
        problem="The user reports poor iPhone battery performance.",
        context="The issue relates to battery life troubleshooting.",
        intent="The user wants clear troubleshooting steps.",
    )

    assert summary.problem
    assert summary.context
    assert summary.intent


def test_summary_input_can_be_created(
    ticket: Ticket,
    built_context: BuiltContext,
) -> None:
    summary_input = SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context=None,
    )

    assert summary_input.ticket == ticket
    assert summary_input.built_context == built_context
    assert summary_input.memory_context is None


def test_summary_output_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Missing context and intent",
        )


# ============================================================
# 2. Prompt construction tests
# ============================================================

def test_build_messages_returns_system_and_human_messages(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()
    messages = agent._build_messages(summary_input)

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


def test_build_messages_includes_ticket_description(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert summary_input.ticket.description in human_message


def test_build_messages_includes_built_context(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert summary_input.built_context.context_text in human_message


def test_build_messages_handles_missing_memory_context(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" in human_message
    assert "None" in human_message


def test_build_messages_includes_memory_context_when_present(
    ticket: Ticket,
    built_context: BuiltContext,
) -> None:
    memory_context = "The user previously tried restarting the device."

    summary_input = SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context=memory_context,
    )

    agent = SummaryAgent()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert memory_context in human_message


# ============================================================
# 3. Agent behavior tests without real LLM call
# ============================================================

class FakeStructuredLLM:
    def invoke(self, messages):
        return SummaryOutput(
            problem="The user reports poor iPhone battery performance.",
            context="The case relates to iPhone battery life troubleshooting.",
            intent="The user wants troubleshooting steps and defect assessment.",
        )


def test_summarize_returns_summary_output(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()
    agent.structured_llm = FakeStructuredLLM()

    result = agent.summarize(summary_input)

    assert isinstance(result, SummaryOutput)
    assert result.problem
    assert result.context
    assert result.intent


def test_summarize_uses_built_messages(
    summary_input: SummaryInput,
    monkeypatch,
) -> None:
    agent = SummaryAgent()
    agent.structured_llm = FakeStructuredLLM()

    called = {"value": False}

    def fake_build_messages(input_data):
        called["value"] = True
        return [
            SystemMessage(content="system"),
            HumanMessage(content="human"),
        ]

    monkeypatch.setattr(agent, "_build_messages", fake_build_messages)

    result = agent.summarize(summary_input)

    assert called["value"] is True
    assert isinstance(result, SummaryOutput)


# ============================================================
# 4. Integration test with real LLM call
# ============================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY is not set"
)
def test_summary_agent_real_llm_call_returns_summary_output(
    summary_input: SummaryInput,
) -> None:
    agent = SummaryAgent()

    result = agent.summarize(summary_input)

    assert isinstance(result, SummaryOutput)
    assert isinstance(result.problem, str)
    assert isinstance(result.context, str)
    assert isinstance(result.intent, str)

    assert result.problem.strip()
    assert result.context.strip()
    assert result.intent.strip()
