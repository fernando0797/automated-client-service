import os
import pytest
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.request_models import Ticket
from src.core.context_models import BuiltContext
from src.core.summary_models import SummaryInput, SummaryOutput
from src.agents.summary_agent import SummaryAgent


# ============================================================
# Helpers
# ============================================================

def make_summary_agent_without_llm() -> SummaryAgent:
    """
    Create a SummaryAgent instance without calling __init__.

    This avoids initializing ChatGoogleGenerativeAI in unit tests,
    so no GOOGLE_API_KEY/GEMINI_API_KEY is required.
    """
    return SummaryAgent.__new__(SummaryAgent)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def ticket() -> Ticket:
    return Ticket(
        ticket_id="test_001",
        turn_id="turn_001",
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


def test_summary_input_accepts_memory_context(
    ticket: Ticket,
    built_context: BuiltContext,
) -> None:
    memory_context = "The user previously tried restarting the device."

    summary_input = SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context=memory_context,
    )

    assert summary_input.memory_context == memory_context


def test_summary_output_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Missing context and intent",
        )


def test_summary_output_rejects_empty_problem() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="",
            context="Valid context.",
            intent="Valid intent.",
        )


def test_summary_output_rejects_empty_context() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Valid problem.",
            context="",
            intent="Valid intent.",
        )


def test_summary_output_rejects_empty_intent() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Valid problem.",
            context="Valid context.",
            intent="",
        )


def test_summary_output_rejects_too_long_problem() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="x" * 501,
            context="Valid context.",
            intent="Valid intent.",
        )


def test_summary_output_accepts_max_length_problem() -> None:
    summary = SummaryOutput(
        problem="x" * 500,
        context="Valid context.",
        intent="Valid intent.",
    )

    assert len(summary.problem) == 500


def test_summary_output_rejects_too_long_context() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Valid problem.",
            context="x" * 1001,
            intent="Valid intent.",
        )


def test_summary_output_accepts_max_length_context() -> None:
    summary = SummaryOutput(
        problem="Valid problem.",
        context="x" * 1000,
        intent="Valid intent.",
    )

    assert len(summary.context) == 1000


def test_summary_output_rejects_too_long_intent() -> None:
    with pytest.raises(ValidationError):
        SummaryOutput(
            problem="Valid problem.",
            context="Valid context.",
            intent="x" * 301,
        )


def test_summary_output_accepts_max_length_intent() -> None:
    summary = SummaryOutput(
        problem="Valid problem.",
        context="Valid context.",
        intent="x" * 300,
    )

    assert len(summary.intent) == 300


def test_summary_input_requires_ticket(
    built_context: BuiltContext,
) -> None:
    with pytest.raises(ValidationError):
        SummaryInput(
            built_context=built_context,
            memory_context=None,
        )


def test_summary_input_requires_built_context(
    ticket: Ticket,
) -> None:
    with pytest.raises(ValidationError):
        SummaryInput(
            ticket=ticket,
            memory_context=None,
        )


# ============================================================
# 2. Prompt construction tests
# ============================================================

def test_build_messages_returns_system_and_human_messages(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


def test_build_messages_includes_ticket_description(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert summary_input.ticket.description in human_message


def test_build_messages_includes_built_context(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert summary_input.built_context.context_text in human_message


def test_build_messages_does_not_include_memory_context_when_missing(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" not in human_message
    assert "None" not in human_message


def test_build_messages_does_not_include_memory_context_when_blank(
    ticket: Ticket,
    built_context: BuiltContext,
) -> None:
    summary_input = SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context="   ",
    )

    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" not in human_message


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

    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    human_message = messages[1].content

    assert "MEMORY CONTEXT" in human_message
    assert memory_context in human_message


def test_build_messages_system_prompt_mentions_summary_fields(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    system_message = messages[0].content

    assert "problem" in system_message
    assert "context" in system_message
    assert "intent" in system_message


def test_build_messages_system_prompt_mentions_length_limits(
    summary_input: SummaryInput,
) -> None:
    agent = make_summary_agent_without_llm()
    messages = agent._build_messages(summary_input)

    system_message = messages[0].content

    assert "500" in system_message
    assert "1000" in system_message
    assert "300" in system_message


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
    agent = make_summary_agent_without_llm()
    agent.structured_llm = FakeStructuredLLM()

    result = agent.summarize(summary_input)

    assert isinstance(result, SummaryOutput)
    assert result.problem
    assert result.context
    assert result.intent
    assert len(result.problem) <= 500
    assert len(result.context) <= 1000
    assert len(result.intent) <= 300


def test_summarize_uses_built_messages(
    summary_input: SummaryInput,
    monkeypatch,
) -> None:
    agent = make_summary_agent_without_llm()
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

@pytest.mark.live_llm
@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY is not set",
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

    assert len(result.problem) <= 500
    assert len(result.context) <= 1000
    assert len(result.intent) <= 300
