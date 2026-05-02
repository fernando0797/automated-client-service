from __future__ import annotations
from typing import List, Dict

from src.core.models import KnowledgeChunk, RetrievalResult
from src.core.request_models import Ticket
from src.rag.embeddings import Embedder
from src.rag.vector_store import VectorStore


class Retriever:
    def __init__(self, chunks: List[KnowledgeChunk], embedder: Embedder, vectorstore: VectorStore):
        self.chunks = chunks
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.embeddings = self.embedder.embed_chunks(self.chunks)
        self.vectorstore.build_index(self.embeddings, self.chunks)
        self.chunk_id_to_index = {
            chunk.chunk_id: num for num, chunk in enumerate(self.chunks)
        }

    def hybrid_retrieve(self, ticket: Ticket, query: str | None = None, k: int = 5, semantic_relative_ratio: float = 1.30) -> List[RetrievalResult]:
        if k <= 0:
            k = 5

        filtered_results = self.filter_retrieve(
            ticket=ticket, query=query, k=k)
        filtered_results.sort(key=lambda x: x.distance)

        semantic_results = self.semantic_retrieve(
            ticket=ticket, query=query, k=k + 2)
        semantic_results.sort(key=lambda x: x.distance)

        if not filtered_results:
            return semantic_results[:k]

        semantic_slots = min(2, max(k - 1, 0))
        guaranteed_filter_k = k - semantic_slots

        selected = filtered_results[:guaranteed_filter_k]
        selected_ids = {result.chunk.chunk_id for result in selected}

        filter_candidate_pool = filtered_results[guaranteed_filter_k:k]
        filter_ids = {result.chunk.chunk_id for result in filtered_results}

        semantic_candidates = [
            result for result in semantic_results
            if result.chunk.chunk_id not in filter_ids
        ]

        reference_pool = filter_candidate_pool if filter_candidate_pool else selected

        if reference_pool:
            worst_filter_distance = max(
                result.distance for result in reference_pool)
            semantic_candidates = [
                result for result in semantic_candidates
                if result.distance <= worst_filter_distance * semantic_relative_ratio
            ]

        remaining_pool = filter_candidate_pool + semantic_candidates
        remaining_pool.sort(key=lambda x: x.distance)

        for result in remaining_pool:
            if len(selected) >= k:
                break

            chunk_id = result.chunk.chunk_id
            if chunk_id not in selected_ids:
                selected.append(result)
                selected_ids.add(chunk_id)

        return selected[:k]

    def filter_retrieve(self, ticket: Ticket, query: str | None = None, k: int | None = None) -> List[RetrievalResult]:
        effective_query = self._build_query(ticket, query)
        query_embedding = self._embed_query(effective_query)

        filter_vectorstore = VectorStore()

        filtered_chunks = self._filter_chunks(ticket)
        if not filtered_chunks:
            return []

        filtered_embeddings = []
        for chunk in filtered_chunks:
            position = self.chunk_id_to_index[chunk.chunk_id]
            filtered_embeddings.append(self.embeddings[position])

        filter_vectorstore.build_index(filtered_embeddings, filtered_chunks)

        if k is None:
            k = len(filtered_chunks)
        elif k <= 0:
            k = 5

        if k > len(filtered_chunks):
            k = len(filtered_chunks)

        results = filter_vectorstore.search_with_scores(query_embedding, k)

        filtered_results = []
        for result in results:
            filtered_results.append(RetrievalResult(
                chunk=result[0], distance=result[1], source="filter"
            ))

        return filtered_results

    def semantic_retrieve(self, ticket: Ticket, query: str | None = None, k: int = 5) -> List[RetrievalResult]:
        if k <= 0:
            k = 5

        if k > len(self.chunks):
            k = len(self.chunks)

        effective_query = self._build_query(ticket, query)
        query_embedding = self._embed_query(effective_query)

        results = self.vectorstore.search_with_scores(query_embedding, k)

        semantic_results = []
        for result in results:
            semantic_results.append(RetrievalResult(
                chunk=result[0], distance=result[1], source="semantic"
            ))

        return semantic_results

    def _filter_chunks(self, ticket: Ticket) -> List[KnowledgeChunk]:
        filtered_chunks = []

        for chunk in self.chunks:
            if chunk.metadata.get("domain") == ticket.domain and chunk.type == "domain":
                filtered_chunks.append(chunk)
            elif chunk.metadata.get("subdomain") == ticket.subdomain and chunk.type == "subdomain":
                filtered_chunks.append(chunk)
            elif chunk.metadata.get("product") == ticket.product and chunk.type == "product":
                filtered_chunks.append(chunk)
            elif chunk.metadata.get("subdomain") == ticket.subdomain and chunk.metadata.get("product") == ticket.product and chunk.type == "cross_doc":
                filtered_chunks.append(chunk)

        return filtered_chunks

    def _embed_query(self, query: str):
        embedding = self.embedder.embed_texts([query])[0]
        return embedding

    def _build_query(self, ticket: Ticket, query: str | None = None) -> str:
        if query is not None and query.strip():
            return query.strip()

        return ticket.description
