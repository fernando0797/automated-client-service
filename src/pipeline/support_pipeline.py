from src.core.config import KNOWLEDGE_PATH, GOOGLE_API_KEY
from src.core.request_models import Ticket
from src.core.memory_models import MemoryUpdateInput
from src.core.retrieval_policy_models import RetrievalPolicyInput
from src.core.query_rewriter_models import QueryRewriterInput
from src.core.retrieval_tool_models import RetrievalToolInput
from src.core.summary_models import SummaryInput
from src.core.response_models import ResponseInput
from src.core.pipeline_models import PipelineOutput

from src.validation.input_validator import InputValidator
from src.memory.memory_store import InMemoryConversationStore
from src.memory.memory_loader import MemoryLoader
from src.rag.retrieval_policy import RetrievalPolicy
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.tools.retriever_tool import RetrieverTool
from src.rag.context_builder import ContextBuilder
from src.agents.summary_agent import SummaryAgent
from src.agents.response_agent import ResponseAgent
from src.agents.memory_agent import MemoryAgent

default_retrieval_k = 5


class SupportPipeline:
    def __init__(self, input_validator: InputValidator, memory_store: InMemoryConversationStore, memory_loader: MemoryLoader,
                 retrieval_policy: RetrievalPolicy, query_rewriter_agent: QueryRewriterAgent, retriever_tool: RetrieverTool,
                 context_builder: ContextBuilder, summary_agent: SummaryAgent, response_agent: ResponseAgent, memory_agent: MemoryAgent):
        self.input_validator = input_validator
        self.memory_store = memory_store
        self.memory_loader = memory_loader
        self.retrieval_policy = retrieval_policy
        self.query_rewriter_agent = query_rewriter_agent
        self.retriever_tool = retriever_tool
        self.context_builder = context_builder
        self.summary_agent = summary_agent
        self.response_agent = response_agent
        self.memory_agent = memory_agent

    def run_turn(self, ticket: Ticket) -> PipelineOutput:
        validated_ticket = self.input_validator.validate(ticket)

        loaded_memory = self.memory_loader.load(validated_ticket.ticket_id)
        previous_conversation_memory = loaded_memory.memory if loaded_memory.has_memory else None
        previous_memory_content = previous_conversation_memory.memory if previous_conversation_memory else None

        retrieval_policy_decision = self.retrieval_policy.decide(
            RetrievalPolicyInput(ticket=validated_ticket, memory_context=previous_memory_content))

        query_rewriter_output = None
        retrieval_tool_output = None
        built_context = None
        summary_output = None

        if retrieval_policy_decision.use_rag is True:

            if retrieval_policy_decision.is_initial_turn is False and previous_memory_content:
                query_rewriter_output = self.query_rewriter_agent.rewrite(
                    query_rewriter_input=QueryRewriterInput(current_description=validated_ticket.description, memory_context=previous_memory_content))

            retrieval_tool_output = self.retriever_tool.invoke(retrieval_tool_input=RetrievalToolInput(
                ticket=validated_ticket, decision=retrieval_policy_decision, query=query_rewriter_output.optimized_query if query_rewriter_output else None, k=default_retrieval_k))
            results = retrieval_tool_output.results

            if results:
                built_context = self.context_builder.build(
                    retrieval_results=results)

                summary_output = self.summary_agent.summarize(summary_input=SummaryInput(
                    ticket=validated_ticket, built_context=built_context, memory_context=previous_memory_content))

        response_output = self.response_agent.generate_response(response_input=ResponseInput(
            ticket=validated_ticket, summary=summary_output, memory_context=previous_memory_content))

        new_conversation_memory = self.memory_agent.update_memory(
            memory_update_input=MemoryUpdateInput(ticket=validated_ticket, previous_memory=previous_conversation_memory, summary=summary_output, response=response_output))

        if validated_ticket.ticket_id:
            self.memory_store.save(
                ticket_id=validated_ticket.ticket_id, memory=new_conversation_memory)

        pipeline_output = PipelineOutput(ticket=validated_ticket, memory_before=previous_conversation_memory,
                                         retrieval_decision=retrieval_policy_decision, query_rewriter_output=query_rewriter_output, retrieval_output=retrieval_tool_output,
                                         built_context=built_context, summary=summary_output, response=response_output, memory_after=new_conversation_memory)
        return pipeline_output
