import os

import pytest
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.core.query_rewriter_models import QueryRewriterInput, QueryRewriterOutput


# ============================================================
# MODEL TESTS
# ============================================================

def test_query_rewriter_input_accepts_valid_data():
    query_input = QueryRewriterInput(
        current_description="It still does not work",
        memory_context="The customer reported that their iPhone battery drains quickly after an update.",
    )

    assert query_input.current_description == "It still does not work"
    assert query_input.memory_context == (
        "The customer reported that their iPhone battery drains quickly after an update."
    )


def test_query_rewriter_output_accepts_valid_data():
    output = QueryRewriterOutput(
        optimized_query="iPhone battery draining quickly after software update"
    )

    assert output.optimized_query == "iPhone battery draining quickly after software update"


def test_query_rewriter_input_rejects_empty_current_description():
    with pytest.raises(ValidationError):
        QueryRewriterInput(
            current_description="",
            memory_context="Previous issue about iPhone battery drain.",
        )


def test_query_rewriter_input_rejects_empty_memory_context():
    with pytest.raises(ValidationError):
        QueryRewriterInput(
            current_description="It still fails",
            memory_context="",
        )


def test_query_rewriter_output_rejects_empty_optimized_query():
    with pytest.raises(ValidationError):
        QueryRewriterOutput(optimized_query="")


def test_query_rewriter_input_strips_whitespace_if_model_validates_it():
    query_input = QueryRewriterInput(
        current_description="   It still fails   ",
        memory_context="   Previous issue about iPhone battery drain.   ",
    )

    assert query_input.current_description == "It still fails"
    assert query_input.memory_context == "Previous issue about iPhone battery drain."


def test_query_rewriter_output_strips_whitespace_if_model_validates_it():
    output = QueryRewriterOutput(
        optimized_query="   iPhone battery drain after software update   "
    )

    assert output.optimized_query == "iPhone battery drain after software update"


# ============================================================
# FAKE LLM CLASSES
# ============================================================

class FakeStructuredLLM:
    def __init__(self, output: QueryRewriterOutput):
        self.output = output
        self.received_messages = None
        self.call_count = 0

    def invoke(self, messages):
        self.received_messages = messages
        self.call_count += 1
        return self.output


class FakeChatGoogleGenerativeAI:
    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model")
        self.temperature = kwargs.get("temperature")
        self.structured_output_schema = None
        self.fake_structured_llm = FakeStructuredLLM(
            QueryRewriterOutput(
                optimized_query="iPhone battery drain after software update"
            )
        )

    def with_structured_output(self, schema):
        self.structured_output_schema = schema
        return self.fake_structured_llm


# ============================================================
# AGENT UNIT TESTS
# ============================================================

def test_agent_initializes_llm_with_expected_defaults(monkeypatch):
    created_instances = []

    class TrackingFakeChatGoogleGenerativeAI(FakeChatGoogleGenerativeAI):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created_instances.append(self)

    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        TrackingFakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    assert len(created_instances) == 1
    assert created_instances[0].model == "gemini-2.5-flash"
    assert created_instances[0].temperature == 0.0
    assert created_instances[0].structured_output_schema is QueryRewriterOutput
    assert agent.structured_llm is created_instances[0].fake_structured_llm


def test_agent_initializes_llm_with_custom_model_and_temperature(monkeypatch):
    created_instances = []

    class TrackingFakeChatGoogleGenerativeAI(FakeChatGoogleGenerativeAI):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created_instances.append(self)

    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        TrackingFakeChatGoogleGenerativeAI,
    )

    QueryRewriterAgent(model_name="custom-model", temperature=0.2)

    assert created_instances[0].model == "custom-model"
    assert created_instances[0].temperature == 0.2


def test_build_messages_returns_system_and_human_messages(monkeypatch):
    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="It still does not work",
        memory_context="The customer reported an iPhone battery drain after an update.",
    )

    messages = agent._build_messages(query_input)

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


def test_build_messages_contains_current_description_and_memory(monkeypatch):
    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="Now it also overheats",
        memory_context="The customer reported fast battery drain on an iPhone after an update.",
    )

    messages = agent._build_messages(query_input)
    human_content = messages[1].content

    assert "CURRENT USER MESSAGE:" in human_content
    assert "Now it also overheats" in human_content
    assert "MEMORY CONTEXT:" in human_content
    assert "fast battery drain" in human_content
    assert "iPhone" in human_content


def test_build_messages_system_prompt_contains_core_boundaries(monkeypatch):
    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="It still fails",
        memory_context="The customer reported a Fitbit sync issue.",
    )

    messages = agent._build_messages(query_input)
    system_content = messages[0].content

    assert "rewrite customer support messages" in system_content.lower()
    assert "semantic search query" in system_content.lower()
    assert "do not answer" in system_content.lower()
    assert "do not invent facts" in system_content.lower()
    assert "prioritize current message" in system_content.lower()
    assert "output in english" in system_content.lower()


def test_build_messages_strips_input_values(monkeypatch):
    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="   It still fails   ",
        memory_context="   Previous issue about iPhone overheating.   ",
    )

    messages = agent._build_messages(query_input)
    human_content = messages[1].content

    assert "   It still fails   " not in human_content
    assert "It still fails" in human_content
    assert "   Previous issue about iPhone overheating.   " not in human_content
    assert "Previous issue about iPhone overheating." in human_content


def test_rewrite_invokes_structured_llm_once(monkeypatch):
    fake_chat_instance = FakeChatGoogleGenerativeAI()

    class FixedFakeChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs):
            pass

        def with_structured_output(self, schema):
            return fake_chat_instance.fake_structured_llm

    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FixedFakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="It still fails",
        memory_context="The customer reported an iPhone battery issue.",
    )

    result = agent.rewrite(query_input)

    assert fake_chat_instance.fake_structured_llm.call_count == 1
    assert isinstance(result, QueryRewriterOutput)
    assert result.optimized_query == "iPhone battery drain after software update"


def test_rewrite_passes_built_messages_to_structured_llm(monkeypatch):
    fake_structured_llm = FakeStructuredLLM(
        QueryRewriterOutput(
            optimized_query="Fitbit Versa not syncing after mobile app update"
        )
    )

    class FixedFakeChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs):
            pass

        def with_structured_output(self, schema):
            return fake_structured_llm

    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FixedFakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="It still does not sync",
        memory_context="The customer reported a Fitbit Versa issue after updating the mobile app.",
    )

    result = agent.rewrite(query_input)

    assert result.optimized_query == "Fitbit Versa not syncing after mobile app update"
    assert fake_structured_llm.received_messages is not None
    assert len(fake_structured_llm.received_messages) == 2
    assert isinstance(fake_structured_llm.received_messages[0], SystemMessage)
    assert isinstance(fake_structured_llm.received_messages[1], HumanMessage)


def test_rewrite_returns_query_rewriter_output(monkeypatch):
    fake_structured_llm = FakeStructuredLLM(
        QueryRewriterOutput(
            optimized_query="Sony headphones Bluetooth battery issue"
        )
    )

    class FixedFakeChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs):
            pass

        def with_structured_output(self, schema):
            return fake_structured_llm

    monkeypatch.setattr(
        "src.agents.query_rewriter_agent.ChatGoogleGenerativeAI",
        FixedFakeChatGoogleGenerativeAI,
    )

    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="It happens only with Bluetooth",
        memory_context="The customer reported a battery issue with Sony headphones.",
    )

    result = agent.rewrite(query_input)

    assert isinstance(result, QueryRewriterOutput)
    assert result.optimized_query == "Sony headphones Bluetooth battery issue"


# ============================================================
# OPTIONAL LIVE LLM INTEGRATION TESTS
# ============================================================

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _live_llm_enabled() -> bool:
    return os.getenv("RUN_LIVE_LLM_TESTS") == "1"


@pytest.mark.live_llm
@pytest.mark.skipif(
    not _live_llm_enabled(),
    reason="Set RUN_LIVE_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_live_rewrite_follow_up_with_memory_returns_useful_query():
    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="Now it also gets hot",
        memory_context=(
            "The customer reported that their iPhone battery drains very quickly "
            "after the latest software update."
        ),
    )

    result = agent.rewrite(query_input)

    assert isinstance(result, QueryRewriterOutput)
    assert result.optimized_query.strip()
    assert len(result.optimized_query) <= 300

    query_lower = result.optimized_query.lower()

    assert "iphone" in query_lower
    assert any(term in query_lower for term in ["battery", "drain"])
    assert any(term in query_lower for term in ["hot", "heat", "overheat"])


@pytest.mark.live_llm
@pytest.mark.skipif(
    not _live_llm_enabled(),
    reason="Set RUN_LIVE_LLM_TESTS=1 to run live LLM integration tests.",
)
def test_live_rewrite_prioritizes_current_message_over_memory_when_contradicted():
    agent = QueryRewriterAgent()

    query_input = QueryRewriterInput(
        current_description="Sorry, it is not an iPhone, it is an iPad",
        memory_context=(
            "The customer reported that their iPhone battery drains very quickly "
            "after the latest software update."
        ),
    )

    result = agent.rewrite(query_input)

    assert isinstance(result, QueryRewriterOutput)
    assert result.optimized_query.strip()
    assert len(result.optimized_query) <= 300

    query_lower = result.optimized_query.lower()

    assert "ipad" in query_lower
