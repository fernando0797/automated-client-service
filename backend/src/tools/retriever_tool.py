from __future__ import annotations

from src.core.retrieval_tool_models import RetrievalToolInput, RetrievalToolOutput
from src.rag.retriever import Retriever


class RetrieverTool:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def invoke(self, retrieval_tool_input: RetrievalToolInput) -> RetrievalToolOutput:
        return self._build_results(retrieval_tool_input=retrieval_tool_input)

    def _build_results(self, retrieval_tool_input: RetrievalToolInput, semantic_relative_ratio: float = 1.30) -> RetrievalToolOutput:
        retrieval_mode = retrieval_tool_input.decision.retrieval_mode
        use_rag = retrieval_tool_input.decision.use_rag

        if retrieval_mode == "none" and use_rag:
            raise ValueError(
                f'If Retrieval Mode is {retrieval_mode}, then Use Rag must be False')
        if retrieval_mode != "none" and not use_rag:
            raise ValueError(
                f'If Retrieval Mode is {retrieval_mode}, then Use Rag must be True')

        if retrieval_mode == "none":
            return RetrievalToolOutput(called=False, mode_used="none")

        raw_query = retrieval_tool_input.query
        optimized_query = (
            raw_query.strip() if raw_query and raw_query.strip() else None)
        effective_query = optimized_query or retrieval_tool_input.ticket.description

        effective_k = retrieval_tool_input.k

        if retrieval_mode == "hybrid":
            results = self.retriever.hybrid_retrieve(
                ticket=retrieval_tool_input.ticket, query=effective_query, k=effective_k, semantic_relative_ratio=semantic_relative_ratio)
            return RetrievalToolOutput(called=True, mode_used="hybrid", optimized_query=optimized_query,
                                       results=results, total_results=len(results))

        elif retrieval_mode == "filter":
            results = self.retriever.filter_retrieve(
                ticket=retrieval_tool_input.ticket, query=effective_query, k=effective_k)
            return RetrievalToolOutput(called=True, mode_used="filter", optimized_query=optimized_query,
                                       results=results, total_results=len(results))

        elif retrieval_mode == "semantic":
            results = self.retriever.semantic_retrieve(
                ticket=retrieval_tool_input.ticket, query=effective_query, k=effective_k)
            return RetrievalToolOutput(called=True, mode_used="semantic", optimized_query=optimized_query,
                                       results=results, total_results=len(results))

        else:
            raise ValueError(f"Unsupported retrieval mode: {retrieval_mode}")
