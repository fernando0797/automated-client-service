from __future__ import annotations

from pathlib import Path
from pprint import pprint

from src.core.config import KNOWLEDGE_PATH
from src.core.request_models import Ticket

from src.validation.input_validator import InputValidator

from src.rag.loader import KnowledgeLoader
from src.rag.chunking import Chunker
from src.rag.embeddings import Embedder
from src.rag.vector_store import VectorStore
from src.rag.retriever import Retriever
from src.rag.context_builder import ContextBuilder

from src.core.summary_models import SummaryInput
from src.agents.summary_agent import SummaryAgent

from src.core.response_models import ResponseInput
from src.agents.response_agent import ResponseAgent


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subsection(title: str) -> None:
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def print_preview(text: str, max_chars: int = 400) -> None:
    clean_text = text.replace("\n", " ")
    if len(clean_text) > max_chars:
        clean_text = clean_text[:max_chars] + "..."
    print(clean_text)


def main() -> None:
    print_section("TFG PIPELINE DEMO")
    print("Running full pipeline:")
    print(
        "Input Validation Layer → Hybrid Retriever → Context Builder "
        "→ Summary Agent → Response Agent"
    )

    # -------------------------------------------------------------------------
    # 1. Example ticket input
    # -------------------------------------------------------------------------
    print_section("1. RAW TICKET INPUT")

    raw_ticket = {
        "ticket_id": "demo-ticket-001",
        "source": "main_demo",
        "description": (
            "My iPhone battery drains very quickly after the latest update. "
            "It also gets warm when I use basic apps like messages or browsing. "
            "What can I do?"
        ),
        "domain": "technical_support",
        "subdomain": "battery_life",
        "product": "iphone",
    }

    pprint(raw_ticket)

    # -------------------------------------------------------------------------
    # 2. Input validation
    # -------------------------------------------------------------------------
    print_section("2. INPUT VALIDATION LAYER")

    taxonomies_path = Path(KNOWLEDGE_PATH) / "taxonomies"
    validator = InputValidator(taxonomies_path=taxonomies_path)

    ticket_candidate = Ticket(**raw_ticket)

    try:
        ticket: Ticket = validator.validate(ticket_candidate)

        print("Ticket validated successfully.")
        print("\nCanonical ticket:")
        pprint(ticket.model_dump())

    except ValueError as error:
        print("Ticket validation failed.")
        print(f"\nError: {error}")
        return

    # -------------------------------------------------------------------------
    # 3. Load knowledge base
    # -------------------------------------------------------------------------
    print_section("3. KNOWLEDGE BASE LOADING")

    loader = KnowledgeLoader(KNOWLEDGE_PATH)
    documents = loader.load_all_documents()

    print(f"Documents loaded: {len(documents)}")

    print_subsection("Sample loaded documents")
    for doc in documents[:3]:
        print(
            {
                "doc_id": doc.doc_id,
                "type": doc.type,
                "metadata": doc.metadata,
                "content_preview": doc.content[:160].replace("\n", " ") + "...",
            }
        )

    # -------------------------------------------------------------------------
    # 4. Chunking
    # -------------------------------------------------------------------------
    print_section("4. CHUNKING")

    chunker = Chunker(documents)
    chunks = chunker.chunk_all_documents()

    print(f"Chunks generated: {len(chunks)}")

    print_subsection("Sample chunks")
    for chunk in chunks[:3]:
        print(
            {
                "chunk_id": chunk.chunk_id,
                "parent_doc_id": chunk.parent_doc_id,
                "type": chunk.type,
                "metadata": chunk.metadata,
                "content_preview": chunk.content[:180].replace("\n", " ") + "...",
            }
        )

    # -------------------------------------------------------------------------
    # 6. Hybrid retrieval
    # -------------------------------------------------------------------------
    print_section("6. HYBRID RETRIEVAL")

    retriever = Retriever(
        chunks=chunks,
        embedder=Embedder(),
        vectorstore=VectorStore(),
    )

    retrieval_results = retriever.hybrid_retrieve(
        ticket=ticket,
        k=5,
    )

    print(f"Retrieval results returned: {len(retrieval_results)}")

    print_subsection("Retrieved chunks trace")
    for i, result in enumerate(retrieval_results, start=1):
        distance = result.distance if result.distance is not None else "N/A"

        print(f"\nResult #{i}")
        print(f"chunk_id: {result.chunk.chunk_id}")
        print(f"parent_doc_id: {result.chunk.parent_doc_id}")
        print(f"type: {result.chunk.type}")
        print(f"source: {result.source}")
        print(f"distance: {distance}")
        print(f"metadata: {result.chunk.metadata}")
        print("content preview:")
        print_preview(result.chunk.content, max_chars=400)

    # -------------------------------------------------------------------------
    # 7. Context Builder
    # -------------------------------------------------------------------------
    print_section("7. CONTEXT BUILDER")

    context_builder = ContextBuilder()
    built_context = context_builder.build(retrieval_results)

    print("Context built successfully.")
    print(f"Total chars: {built_context.total_chars}")
    print(f"Results used: {len(built_context.results_used)}")

    print_subsection("Context text preview")
    print(built_context.context_text[:1500])

    # -------------------------------------------------------------------------
    # 8. Summary Agent
    # -------------------------------------------------------------------------
    print_section("8. SUMMARY AGENT")

    summary_agent = SummaryAgent()

    summary_input = SummaryInput(
        ticket=ticket,
        built_context=built_context,
        memory_context=None,
    )

    summary_output = summary_agent.summarize(summary_input)

    print("Summary generated successfully.")

    print_subsection("SummaryOutput")
    print("Problem:")
    print(summary_output.problem)

    print("\nContext:")
    print(summary_output.context)

    print("\nIntent:")
    print(summary_output.intent)

    # -------------------------------------------------------------------------
    # 9. Response Agent
    # -------------------------------------------------------------------------
    print_section("9. RESPONSE AGENT")

    response_agent = ResponseAgent()

    response_input = ResponseInput(
        summary=summary_output,
        built_context=built_context,
        memory_context=None,
    )

    response_output = response_agent.generate_response(response_input)

    print("Response generated successfully.")

    print_subsection("ResponseOutput metadata")
    print(f"Tone: {response_output.tone}")
    print(f"Resolution type: {response_output.resolution_type}")
    print(f"Requires escalation: {response_output.requires_escalation}")
    print(f"Escalation channel: {response_output.escalation_channel}")
    print(f"Confidence: {response_output.confidence}")

    print_subsection("Final user response")
    print(response_output.response)

    # -------------------------------------------------------------------------
    # 10. Final compact trace
    # -------------------------------------------------------------------------
    print_section("10. COMPACT PIPELINE TRACE")

    trace = {
        "ticket_id": ticket.ticket_id,
        "domain": ticket.domain,
        "subdomain": ticket.subdomain,
        "product": ticket.product,
        "documents_loaded": len(documents),
        "chunks_generated": len(chunks),
        "retrieval_results": len(retrieval_results),
        "retrieval_sources": [result.source for result in retrieval_results],
        "context_total_chars": built_context.total_chars,
        "summary_problem": summary_output.problem,
        "summary_intent": summary_output.intent,
        "response_tone": response_output.tone,
        "resolution_type": response_output.resolution_type,
        "requires_escalation": response_output.requires_escalation,
        "escalation_channel": response_output.escalation_channel,
        "confidence": response_output.confidence,
    }

    pprint(trace)

    print_section("PIPELINE FINISHED")


if __name__ == "__main__":
    main()
