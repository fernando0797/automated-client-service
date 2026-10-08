from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.agents.memory_agent import MemoryAgent
from src.agents.query_rewriter_agent import QueryRewriterAgent
from src.agents.response_agent import ResponseAgent
from src.agents.summary_agent import SummaryAgent
from src.conversation.conversation_updater import ConversationUpdater
from src.core.config import (
    KNOWLEDGE_PATH,
    MAX_RAG_CALLS_PER_TICKET,
    MAX_TURNS_PER_TICKET,
    TAXONOMIES_PATH,
)
from src.graph.graph_runner import SupportGraphRunner
from src.persistence.database import create_db_session
from src.persistence.repositories.conversation_memory_repository import (
    SQLConversationMemoryStore,
)
from src.persistence.repositories.conversation_state_repository import (
    SQLConversationStateStore,
)
from src.persistence.repositories.turn_trace_repository import SQLTraceStore
from src.rag.chunking import Chunker
from src.rag.context_builder import ContextBuilder
from src.rag.embeddings import Embedder
from src.rag.loader import KnowledgeLoader
from src.rag.retrieval_policy import RetrievalPolicy
from src.rag.retriever import Retriever
from src.rag.vector_store import VectorStore
from src.tools.retriever_tool import RetrieverTool
from src.validation.input_validator import InputValidator


@dataclass
class AppServices:
    input_validator: InputValidator
    conversation_updater: ConversationUpdater
    retrieval_policy: RetrievalPolicy
    query_rewriter_agent: QueryRewriterAgent
    retriever_tool: RetrieverTool
    context_builder: ContextBuilder
    summary_agent: SummaryAgent
    response_agent: ResponseAgent
    memory_agent: MemoryAgent


def get_api_status() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "support-chatbot-api",
    }


def get_api_db_session() -> Generator[Session, None, None]:
    session = create_db_session()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection(session: Session) -> bool:
    session.execute(text("SELECT 1"))
    return True


def build_retriever_tool() -> RetrieverTool:
    loader = KnowledgeLoader(knowledge_base_path=KNOWLEDGE_PATH)
    knowledge_documents = loader.load_all_documents()

    chunker = Chunker(knowledge_documents)
    knowledge_chunks = chunker.chunk_all_documents()

    embedder = Embedder()
    vectorstore = VectorStore()

    retriever = Retriever(chunks=knowledge_chunks, embedder=embedder, vectorstore=vectorstore)

    return RetrieverTool(retriever=retriever)


def build_app_services() -> AppServices:
    input_validator = InputValidator(taxonomies_path=TAXONOMIES_PATH)

    conversation_updater = ConversationUpdater()
    retrieval_policy = RetrievalPolicy()

    query_rewriter_agent = QueryRewriterAgent()
    retriever_tool = build_retriever_tool()

    context_builder = ContextBuilder()

    summary_agent = SummaryAgent()
    response_agent = ResponseAgent()
    memory_agent = MemoryAgent()

    return AppServices(
        input_validator=input_validator,
        conversation_updater=conversation_updater,
        retrieval_policy=retrieval_policy,
        query_rewriter_agent=query_rewriter_agent,
        retriever_tool=retriever_tool,
        context_builder=context_builder,
        summary_agent=summary_agent,
        response_agent=response_agent,
        memory_agent=memory_agent,
    )


def build_support_graph_runner(session: Session, app_services: AppServices) -> SupportGraphRunner:
    conversation_state_store = SQLConversationStateStore(db=session)
    memory_store = SQLConversationMemoryStore(db=session)
    trace_store = SQLTraceStore(db=session)

    return SupportGraphRunner(
        input_validator=app_services.input_validator,
        conversation_state_store=conversation_state_store,
        conversation_updater=app_services.conversation_updater,
        memory_store=memory_store,
        retrieval_policy=app_services.retrieval_policy,
        query_rewriter_agent=app_services.query_rewriter_agent,
        retriever_tool=app_services.retriever_tool,
        context_builder=app_services.context_builder,
        summary_agent=app_services.summary_agent,
        response_agent=app_services.response_agent,
        memory_agent=app_services.memory_agent,
        max_turns_per_ticket=MAX_TURNS_PER_TICKET,
        max_rag_calls_per_ticket=MAX_RAG_CALLS_PER_TICKET,
        trace_store=trace_store,
    )
