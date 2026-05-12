from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.core.context_models import BuiltContext
from src.core.conversation_state_models import ConversationState
from src.core.default_models import PredefinedClosingResponse, PredefinedEscalationResponse
from src.core.memory_models import ConversationMemory, LoadedMemory
from src.core.query_rewriter_models import QueryRewriterOutput
from src.core.request_models import Ticket
from src.core.response_models import ResponseOutput
from src.core.retrieval_policy_models import RetrievalPolicyDecision
from src.core.retrieval_tool_models import RetrievalToolOutput
from src.core.summary_models import SummaryOutput
from src.graph.nodes import (
    already_closed_response_node,
    already_escalated_response_node,
    force_escalation_response_node,
    make_build_context_node,
    make_build_summary_node,
    make_classify_initial_route_node,
    make_generate_new_memory_node,
    make_generate_response_output_node,
    make_load_conversation_state_node,
    make_load_memory_node,
    make_retrieval_policy_decision_node,
    make_retrieve_results_tool,
    make_rewrite_query_node,
    make_save_conversation_memory_node,
    make_save_conversation_state_node,
    make_update_conversation_node,
    make_validate_input_ticket_node,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def make_ticket(
    *,
    ticket_id: str = "ticket_1",
    turn_id: str = "turn_1",
    description: str = "My phone is overheating when charging.",
) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        turn_id=turn_id,
        source="web",
        description=description,
        domain="technical_support",
        subdomain="device_overheating",
        product="smartphone",
    )


def make_conversation_state(
    *,
    ticket_id: str = "ticket_1",
    turn_count: int = 0,
    rag_call_count: int = 0,
    status: str = "active",
) -> ConversationState:
    now = datetime.now(timezone.utc).isoformat()

    return ConversationState(
        ticket_id=ticket_id,
        turn_count=turn_count,
        rag_call_count=rag_call_count,
        last_turn_id=None,
        status=status,
        created_at=now,
        updated_at=now,
    )


def make_loaded_memory_with_content() -> LoadedMemory:
    return LoadedMemory(
        has_memory=True,
        memory=ConversationMemory(memory="The user previously reported overheating."),
    )


def make_loaded_memory_empty() -> LoadedMemory:
    return LoadedMemory(
        has_memory=False,
        memory=None,
    )


def make_response_output() -> ResponseOutput:
    return ResponseOutput(
        response="Please check the charger and avoid using the phone while charging.",
        tone="professional",
        resolution_type="troubleshooting_steps",
        requires_escalation=False,
        should_close=False,
        confidence=0.8,
        escalation_channel="none",
    )


def make_retrieval_decision(
    *,
    use_rag: bool = True,
    use_memory: bool = False,
    is_initial_turn: bool = True,
    retrieval_mode: str = "semantic",
) -> RetrievalPolicyDecision:
    return RetrievalPolicyDecision(
        use_rag=use_rag,
        use_memory=use_memory,
        is_initial_turn=is_initial_turn,
        retrieval_mode=retrieval_mode,
        decision_type="metadata_and_description",
        reason="test decision",
    )


def make_summary() -> SummaryOutput:
    return SummaryOutput(
        problem="Phone overheats while charging.",
        context="The issue is related to charging and device temperature.",
        intent="User wants troubleshooting steps.",
    )


def make_built_context() -> BuiltContext:
    return BuiltContext.model_construct(
        context_text="Relevant troubleshooting context.",
        results_used=[],
        truncated=False,
        total_chars=35,
    )


def make_retrieval_output_with_results() -> RetrievalToolOutput:
    return RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[SimpleNamespace(chunk_id="chunk_1", text="test result")],
        total_results=1,
    )


def assert_node_trace(result: dict, expected_node: str) -> None:
    assert result["nodes_executed"] == [expected_node]


# ---------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------


class FakeInputValidator:
    def __init__(self):
        self.called_with = None

    def validate(self, ticket: Ticket) -> Ticket:
        self.called_with = ticket
        return ticket.model_copy(update={"description": ticket.description.strip()})


class FakeConversationStateRepository:
    def __init__(self, state: ConversationState | None):
        self.state = state
        self.called_with_get = None
        self.saved_ticket_id = None
        self.saved_state = None

    def get(self, ticket_id: str | None) -> ConversationState | None:
        self.called_with_get = ticket_id
        return self.state

    def save(self, ticket_id: str, state: ConversationState) -> None:
        self.saved_ticket_id = ticket_id
        self.saved_state = state


class FakeConversationUpdater:
    def __init__(self, new_state: ConversationState):
        self.new_state = new_state
        self.called_with = None

    def update_state(self, **kwargs) -> ConversationState:
        self.called_with = kwargs
        return self.new_state


class FakeMemoryRepository:
    def __init__(self, loaded_memory: LoadedMemory | None = None):
        self.loaded_memory = loaded_memory or make_loaded_memory_empty()
        self.called_with_load = None
        self.saved_ticket_id = None
        self.saved_memory = None

    def load(self, ticket_id: str | None) -> LoadedMemory:
        self.called_with_load = ticket_id
        return self.loaded_memory

    def save(self, ticket_id: str, memory: ConversationMemory) -> None:
        self.saved_ticket_id = ticket_id
        self.saved_memory = memory


class FakeResponseAgent:
    def __init__(self, response: ResponseOutput):
        self.response = response
        self.called_with = None

    def generate_response(self, response_input):
        self.called_with = response_input
        return self.response


class FakeMemoryAgent:
    def __init__(self, memory: ConversationMemory):
        self.memory = memory
        self.called_with = None

    def update_memory(self, memory_update_input):
        self.called_with = memory_update_input
        return self.memory


class FakeRetrievalPolicy:
    def __init__(self, decision: RetrievalPolicyDecision):
        self.decision = decision
        self.called_with = None

    def decide(self, policy_input):
        self.called_with = policy_input
        return self.decision


class FakeQueryRewriterAgent:
    def __init__(self, output: QueryRewriterOutput):
        self.output = output
        self.called_with = None

    def rewrite(self, query_rewriter_input):
        self.called_with = query_rewriter_input
        return self.output


class FakeRetrieverTool:
    def __init__(self, output: RetrievalToolOutput):
        self.output = output
        self.called_with = None

    def invoke(self, retrieval_tool_input):
        self.called_with = retrieval_tool_input
        return self.output


class FakeContextBuilder:
    def __init__(self, context: BuiltContext):
        self.context = context
        self.called_with = None

    def build(self, retrieval_results):
        self.called_with = retrieval_results
        return self.context


class FakeSummaryAgent:
    def __init__(self, summary: SummaryOutput):
        self.summary = summary
        self.called_with = None

    def summarize(self, summary_input):
        self.called_with = summary_input
        return self.summary


# ---------------------------------------------------------------------
# validate_input_ticket_node
# ---------------------------------------------------------------------


def test_validate_input_ticket_node_updates_ticket():
    ticket = make_ticket(description="  My phone is overheating.  ")
    validator = FakeInputValidator()
    node = make_validate_input_ticket_node(validator)

    result = node({"ticket": ticket})

    assert result["ticket"].description == "My phone is overheating."
    assert validator.called_with == ticket
    assert_node_trace(result, "validate_input_ticket")


def test_validate_input_ticket_node_raises_without_ticket():
    node = make_validate_input_ticket_node(FakeInputValidator())

    with pytest.raises(ValueError, match="ticket is required"):
        node({})


# ---------------------------------------------------------------------
# load_conversation_state_node
# ---------------------------------------------------------------------


def test_load_conversation_state_node_sets_previous_state_when_state_exists():
    ticket = make_ticket()
    state = make_conversation_state()
    repository = FakeConversationStateRepository(state)
    node = make_load_conversation_state_node(repository)

    result = node({"ticket": ticket})

    assert result["previous_conversation_state"] == state
    assert repository.called_with_get == ticket.ticket_id
    assert_node_trace(result, "load_conversation_state")


def test_load_conversation_state_node_creates_initial_state_when_state_does_not_exist():
    ticket = make_ticket()
    repository = FakeConversationStateRepository(state=None)
    node = make_load_conversation_state_node(repository)

    result = node({"ticket": ticket})

    previous_state = result["previous_conversation_state"]

    assert previous_state.ticket_id == ticket.ticket_id
    assert previous_state.turn_count == 0
    assert previous_state.rag_call_count == 0
    assert previous_state.last_turn_id is None
    assert previous_state.status == "active"
    assert repository.called_with_get == ticket.ticket_id
    assert_node_trace(result, "load_conversation_state")


def test_load_conversation_state_node_raises_without_ticket():
    node = make_load_conversation_state_node(
        FakeConversationStateRepository(make_conversation_state())
    )

    with pytest.raises(ValueError, match="ticket is required"):
        node({})


def test_load_conversation_state_node_raises_without_ticket_id():
    ticket = make_ticket(ticket_id="")
    node = make_load_conversation_state_node(
        FakeConversationStateRepository(make_conversation_state())
    )

    with pytest.raises(ValueError, match="ticket_id is required"):
        node({"ticket": ticket})


# ---------------------------------------------------------------------
# classify_initial_route_node
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "conversation_state, expected_route",
    [
        (make_conversation_state(status="closed"), "already_closed"),
        (make_conversation_state(status="escalated"), "already_escalated"),
        (make_conversation_state(turn_count=5, rag_call_count=0, status="active"), "force_escalation"),
        (make_conversation_state(turn_count=1, rag_call_count=3, status="active"), "rag_limit_reached"),
        (make_conversation_state(turn_count=1, rag_call_count=1, status="active"), "active"),
    ],
)
def test_classify_initial_route_node_sets_expected_route(conversation_state, expected_route):
    node = make_classify_initial_route_node(
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
    )

    result = node({"previous_conversation_state": conversation_state})

    assert result["initial_route"] == expected_route
    assert_node_trace(result, "classify_initial_route")


def test_classify_initial_route_node_prioritizes_closed_over_limits():
    state = make_conversation_state(
        status="closed",
        turn_count=99,
        rag_call_count=99,
    )
    node = make_classify_initial_route_node(
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
    )

    result = node({"previous_conversation_state": state})

    assert result["initial_route"] == "already_closed"
    assert_node_trace(result, "classify_initial_route")


def test_classify_initial_route_node_prioritizes_escalated_over_limits():
    state = make_conversation_state(
        status="escalated",
        turn_count=99,
        rag_call_count=99,
    )
    node = make_classify_initial_route_node(
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
    )

    result = node({"previous_conversation_state": state})

    assert result["initial_route"] == "already_escalated"
    assert_node_trace(result, "classify_initial_route")


def test_classify_initial_route_node_raises_without_previous_state():
    node = make_classify_initial_route_node(
        max_turns_per_ticket=5,
        max_rag_calls_per_ticket=3,
    )

    with pytest.raises(ValueError, match="previous_conversation_state is required"):
        node({})


# ---------------------------------------------------------------------
# predefined response nodes
# ---------------------------------------------------------------------


def test_already_closed_response_node_returns_predefined_closing_response():
    result = already_closed_response_node({})

    assert isinstance(result["response"], PredefinedClosingResponse)
    assert_node_trace(result, "already_closed_response")


def test_already_escalated_response_node_returns_predefined_escalation_response():
    result = already_escalated_response_node({})

    assert isinstance(result["response"], PredefinedEscalationResponse)
    assert_node_trace(result, "already_escalated_response")


def test_force_escalation_response_node_returns_predefined_escalation_response():
    result = force_escalation_response_node({})

    assert isinstance(result["response"], PredefinedEscalationResponse)
    assert_node_trace(result, "force_escalation_response")


# ---------------------------------------------------------------------
# update_conversation_node
# ---------------------------------------------------------------------


def test_update_conversation_node_sets_conversation_state_after_with_response_output():
    previous_state = make_conversation_state()
    new_state = make_conversation_state(turn_count=1)
    updater = FakeConversationUpdater(new_state)
    node = make_update_conversation_node(updater)
    ticket = make_ticket()
    response = make_response_output()
    retrieval_decision = make_retrieval_decision()

    result = node(
        {
            "ticket": ticket,
            "previous_conversation_state": previous_state,
            "retrieval_decision": retrieval_decision,
            "response": response,
        }
    )

    assert result["conversation_state_after"] == new_state
    assert updater.called_with["response"] == response
    assert updater.called_with["predefined_closing_response"] is None
    assert updater.called_with["predefined_escalation_response"] is None
    assert_node_trace(result, "update_conversation")


def test_update_conversation_node_sets_conversation_state_after_with_predefined_closing():
    previous_state = make_conversation_state(status="closed")
    new_state = previous_state
    updater = FakeConversationUpdater(new_state)
    node = make_update_conversation_node(updater)
    response = PredefinedClosingResponse(response="Ticket already closed.")

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_state": previous_state,
            "response": response,
        }
    )

    assert result["conversation_state_after"] == new_state
    assert updater.called_with["response"] is None
    assert updater.called_with["predefined_closing_response"] == response
    assert_node_trace(result, "update_conversation")


def test_update_conversation_node_sets_conversation_state_after_with_predefined_escalation():
    previous_state = make_conversation_state()
    new_state = make_conversation_state(status="escalated")
    updater = FakeConversationUpdater(new_state)
    node = make_update_conversation_node(updater)
    response = PredefinedEscalationResponse(response="Escalating.")

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_state": previous_state,
            "response": response,
        }
    )

    assert result["conversation_state_after"] == new_state
    assert updater.called_with["response"] is None
    assert updater.called_with["predefined_escalation_response"] == response
    assert_node_trace(result, "update_conversation")


@pytest.mark.parametrize(
    "state, error",
    [
        ({}, "previous_conversation_state is required"),
        ({"previous_conversation_state": make_conversation_state()}, "ticket is required"),
        (
            {
                "previous_conversation_state": make_conversation_state(),
                "ticket": make_ticket(),
            },
            "response is required",
        ),
    ],
)
def test_update_conversation_node_raises_for_missing_required_state(state, error):
    node = make_update_conversation_node(FakeConversationUpdater(make_conversation_state()))

    with pytest.raises(ValueError, match=error):
        node(state)


# ---------------------------------------------------------------------
# save_conversation_state_node
# ---------------------------------------------------------------------


def test_save_conversation_state_node_saves_state():
    ticket = make_ticket()
    state = make_conversation_state()
    repository = FakeConversationStateRepository(state=None)
    node = make_save_conversation_state_node(repository)

    result = node(
        {
            "ticket": ticket,
            "conversation_state_after": state,
        }
    )

    assert result["nodes_executed"] == ["save_conversation_state"]
    assert repository.saved_ticket_id == ticket.ticket_id
    assert repository.saved_state == state


def test_save_conversation_state_node_raises_without_ticket():
    node = make_save_conversation_state_node(FakeConversationStateRepository(state=None))

    with pytest.raises(ValueError, match="ticket is required"):
        node({"conversation_state_after": make_conversation_state()})


def test_save_conversation_state_node_raises_without_state_after():
    node = make_save_conversation_state_node(FakeConversationStateRepository(state=None))

    with pytest.raises(ValueError, match="conversation_state_after is required"):
        node({"ticket": make_ticket()})


def test_save_conversation_state_node_raises_without_ticket_id():
    ticket = make_ticket(ticket_id="")
    node = make_save_conversation_state_node(FakeConversationStateRepository(state=None))

    with pytest.raises(ValueError, match="ticket_id is required"):
        node(
            {
                "ticket": ticket,
                "conversation_state_after": make_conversation_state(),
            }
        )


# ---------------------------------------------------------------------
# memory load/save nodes
# ---------------------------------------------------------------------


def test_load_memory_node_sets_previous_conversation_memory():
    ticket = make_ticket()
    loaded_memory = make_loaded_memory_with_content()
    repository = FakeMemoryRepository(loaded_memory)
    node = make_load_memory_node(repository)

    result = node({"ticket": ticket})

    assert result["previous_conversation_memory"] == loaded_memory
    assert repository.called_with_load == ticket.ticket_id
    assert_node_trace(result, "load_memory")


def test_load_memory_node_raises_without_ticket():
    node = make_load_memory_node(FakeMemoryRepository(make_loaded_memory_empty()))

    with pytest.raises(ValueError, match="ticket is required"):
        node({})


def test_load_memory_node_raises_without_ticket_id():
    ticket = make_ticket(ticket_id="")
    node = make_load_memory_node(FakeMemoryRepository(make_loaded_memory_empty()))

    with pytest.raises(ValueError, match="ticket_id is required"):
        node({"ticket": ticket})


def test_save_conversation_memory_node_saves_memory():
    ticket = make_ticket()
    memory = ConversationMemory(memory="Updated memory.")
    repository = FakeMemoryRepository()
    node = make_save_conversation_memory_node(repository)

    result = node(
        {
            "ticket": ticket,
            "memory_after": memory,
        }
    )

    assert result["nodes_executed"] == ["save_conversation_memory"]
    assert repository.saved_ticket_id == ticket.ticket_id
    assert repository.saved_memory == memory


def test_save_conversation_memory_node_raises_without_ticket():
    node = make_save_conversation_memory_node(FakeMemoryRepository())

    with pytest.raises(ValueError, match="ticket is required"):
        node({"memory_after": ConversationMemory(memory="Updated memory.")})


def test_save_conversation_memory_node_raises_without_memory_after():
    node = make_save_conversation_memory_node(FakeMemoryRepository())

    with pytest.raises(ValueError, match="new memory is required"):
        node({"ticket": make_ticket()})


def test_save_conversation_memory_node_raises_without_ticket_id():
    ticket = make_ticket(ticket_id="")
    node = make_save_conversation_memory_node(FakeMemoryRepository())

    with pytest.raises(ValueError, match="ticket_id is required"):
        node(
            {
                "ticket": ticket,
                "memory_after": ConversationMemory(memory="Updated memory."),
            }
        )


# ---------------------------------------------------------------------
# generate_response_output_node
# ---------------------------------------------------------------------


def test_generate_response_output_node_sets_response_with_memory():
    response = make_response_output()
    agent = FakeResponseAgent(response)
    node = make_generate_response_output_node(agent)

    result = node(
        {
            "ticket": make_ticket(),
            "summary": make_summary(),
            "previous_conversation_memory": make_loaded_memory_with_content(),
        }
    )

    assert result["response"] == response
    assert agent.called_with.memory_context == "The user previously reported overheating."
    assert_node_trace(result, "generate_response_output")


def test_generate_response_output_node_sets_response_without_memory():
    response = make_response_output()
    agent = FakeResponseAgent(response)
    node = make_generate_response_output_node(agent)

    result = node(
        {
            "ticket": make_ticket(),
            "summary": None,
            "previous_conversation_memory": make_loaded_memory_empty(),
        }
    )

    assert result["response"] == response
    assert agent.called_with.memory_context is None
    assert_node_trace(result, "generate_response_output")


def test_generate_response_output_node_raises_without_ticket():
    node = make_generate_response_output_node(FakeResponseAgent(make_response_output()))

    with pytest.raises(ValueError, match="ticket is required"):
        node({"previous_conversation_memory": make_loaded_memory_empty()})


def test_generate_response_output_node_raises_without_loaded_memory():
    node = make_generate_response_output_node(FakeResponseAgent(make_response_output()))

    with pytest.raises(ValueError, match="previous_conversation_memory is required"):
        node({"ticket": make_ticket()})


# ---------------------------------------------------------------------
# generate_new_memory_node
# ---------------------------------------------------------------------


def test_generate_new_memory_node_sets_memory_after():
    new_memory = ConversationMemory(memory="Updated memory.")
    memory_agent = FakeMemoryAgent(new_memory)
    node = make_generate_new_memory_node(memory_agent)
    response = make_response_output()

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_memory": make_loaded_memory_with_content(),
            "summary": make_summary(),
            "response": response,
        }
    )

    assert result["memory_after"] == new_memory
    assert memory_agent.called_with.response == response
    assert_node_trace(result, "generate_new_memory")


def test_generate_new_memory_node_uses_none_previous_memory_when_no_memory_exists():
    new_memory = ConversationMemory(memory="New memory.")
    memory_agent = FakeMemoryAgent(new_memory)
    node = make_generate_new_memory_node(memory_agent)

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_memory": make_loaded_memory_empty(),
            "summary": None,
            "response": make_response_output(),
        }
    )

    assert result["memory_after"] == new_memory
    assert memory_agent.called_with.previous_memory is None
    assert_node_trace(result, "generate_new_memory")


def test_generate_new_memory_node_raises_without_response_output():
    node = make_generate_new_memory_node(FakeMemoryAgent(ConversationMemory(memory="x")))

    with pytest.raises(ValueError, match="ResponseOutput"):
        node(
            {
                "ticket": make_ticket(),
                "previous_conversation_memory": make_loaded_memory_empty(),
                "response": PredefinedClosingResponse(response="Closed."),
            }
        )


# ---------------------------------------------------------------------
# retrieval_policy_decision_node
# ---------------------------------------------------------------------


def test_retrieval_policy_decision_node_sets_decision_with_memory():
    decision = make_retrieval_decision()
    policy = FakeRetrievalPolicy(decision)
    node = make_retrieval_policy_decision_node(policy)

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_memory": make_loaded_memory_with_content(),
        }
    )

    assert result["retrieval_decision"] == decision
    assert policy.called_with.memory_context == "The user previously reported overheating."
    assert_node_trace(result, "retrieval_policy_decision")


def test_retrieval_policy_decision_node_sets_decision_without_memory():
    decision = make_retrieval_decision()
    policy = FakeRetrievalPolicy(decision)
    node = make_retrieval_policy_decision_node(policy)

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_memory": make_loaded_memory_empty(),
        }
    )

    assert result["retrieval_decision"] == decision
    assert policy.called_with.memory_context is None
    assert_node_trace(result, "retrieval_policy_decision")


# ---------------------------------------------------------------------
# rewrite_query_node
# ---------------------------------------------------------------------


def test_rewrite_query_node_sets_query_rewriter_output():
    output = QueryRewriterOutput(optimized_query="phone overheating while charging")
    agent = FakeQueryRewriterAgent(output)
    node = make_rewrite_query_node(agent)

    result = node(
        {
            "ticket": make_ticket(),
            "previous_conversation_memory": make_loaded_memory_with_content(),
        }
    )

    assert result["query_rewriter_output"] == output
    assert agent.called_with.current_description == "My phone is overheating when charging."
    assert agent.called_with.memory_context == "The user previously reported overheating."
    assert_node_trace(result, "rewrite_query")


def test_rewrite_query_node_raises_without_memory_content():
    node = make_rewrite_query_node(
        FakeQueryRewriterAgent(QueryRewriterOutput(optimized_query="query"))
    )

    with pytest.raises(ValueError, match="requires previous memory"):
        node(
            {
                "ticket": make_ticket(),
                "previous_conversation_memory": make_loaded_memory_empty(),
            }
        )


# ---------------------------------------------------------------------
# retrieve_results_tool_node
# ---------------------------------------------------------------------


def test_retrieve_results_tool_uses_rewritten_query_when_available():
    retrieval_output = make_retrieval_output_with_results()
    tool = FakeRetrieverTool(retrieval_output)
    node = make_retrieve_results_tool(tool)
    query_output = QueryRewriterOutput(optimized_query="optimized overheating query")

    result = node(
        {
            "ticket": make_ticket(),
            "retrieval_decision": make_retrieval_decision(),
            "query_rewriter_output": query_output,
        }
    )

    assert result["retrieval_output"] == retrieval_output
    assert tool.called_with.query == "optimized overheating query"
    assert_node_trace(result, "retrieve_results_tool")


def test_retrieve_results_tool_uses_ticket_description_without_rewritten_query():
    retrieval_output = make_retrieval_output_with_results()
    tool = FakeRetrieverTool(retrieval_output)
    node = make_retrieve_results_tool(tool)
    ticket = make_ticket()

    result = node(
        {
            "ticket": ticket,
            "retrieval_decision": make_retrieval_decision(),
        }
    )

    assert result["retrieval_output"] == retrieval_output
    assert tool.called_with.query == ticket.description
    assert_node_trace(result, "retrieve_results_tool")


def test_retrieve_results_tool_raises_without_retrieval_decision():
    node = make_retrieve_results_tool(FakeRetrieverTool(make_retrieval_output_with_results()))

    with pytest.raises(ValueError, match="retrieval_decision is required"):
        node({"ticket": make_ticket()})


# ---------------------------------------------------------------------
# build_context_node
# ---------------------------------------------------------------------


def test_build_context_node_sets_built_context():
    context = make_built_context()
    builder = FakeContextBuilder(context)
    node = make_build_context_node(builder)
    retrieval_output = make_retrieval_output_with_results()

    result = node({"retrieval_output": retrieval_output})

    assert result["built_context"] == context
    assert builder.called_with == retrieval_output.results
    assert_node_trace(result, "build_context")


def test_build_context_node_raises_without_retrieval_output():
    node = make_build_context_node(FakeContextBuilder(make_built_context()))

    with pytest.raises(ValueError, match="retrieval_output is required"):
        node({})


def test_build_context_node_raises_with_empty_results():
    node = make_build_context_node(FakeContextBuilder(make_built_context()))
    retrieval_output = RetrievalToolOutput.model_construct(
        called=True,
        mode_used="semantic",
        optimized_query=None,
        results=[],
        total_results=0,
    )

    with pytest.raises(ValueError, match="must not be empty"):
        node({"retrieval_output": retrieval_output})


# ---------------------------------------------------------------------
# build_summary_node
# ---------------------------------------------------------------------


def test_build_summary_node_sets_summary_with_memory():
    summary = make_summary()
    agent = FakeSummaryAgent(summary)
    node = make_build_summary_node(agent)

    result = node(
        {
            "ticket": make_ticket(),
            "built_context": make_built_context(),
            "previous_conversation_memory": make_loaded_memory_with_content(),
        }
    )

    assert result["summary"] == summary
    assert agent.called_with.memory_context == "The user previously reported overheating."
    assert_node_trace(result, "build_summary")


def test_build_summary_node_sets_summary_without_memory():
    summary = make_summary()
    agent = FakeSummaryAgent(summary)
    node = make_build_summary_node(agent)

    result = node(
        {
            "ticket": make_ticket(),
            "built_context": make_built_context(),
            "previous_conversation_memory": make_loaded_memory_empty(),
        }
    )

    assert result["summary"] == summary
    assert agent.called_with.memory_context is None
    assert_node_trace(result, "build_summary")


def test_build_summary_node_raises_without_built_context():
    node = make_build_summary_node(FakeSummaryAgent(make_summary()))

    with pytest.raises(ValueError, match="built_context is required"):
        node(
            {
                "ticket": make_ticket(),
                "previous_conversation_memory": make_loaded_memory_empty(),
            }
        )
