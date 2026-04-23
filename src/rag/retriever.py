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
            chunk.chunk_id: num for num, chunk in enumerate(self.chunks)}

    def hybrid_retrieve(self, ticket: Ticket, k: int = 5) -> List[RetrievalResult]:
        if k <= 0:
            k = 5

        filtered_results = self.filter_retrieve(ticket, k)
        semantic_results = self.semantic_retrieve(ticket, k)

        total_results: Dict[str, RetrievalResult] = {}

        for result in filtered_results:
            chunk_id = result.chunk.chunk_id
            total_results[chunk_id] = RetrievalResult(
                chunk=result.chunk, distance=result.distance, source=result.source)

        for result in semantic_results:
            chunk_id = result.chunk.chunk_id

            if chunk_id in total_results:
                total_results[chunk_id].source = "hybrid"
                total_results[chunk_id].distance = min(
                    total_results[chunk_id].distance, result.distance)
            else:
                total_results[chunk_id] = RetrievalResult(
                    chunk=result.chunk, distance=result.distance, source=result.source)

        final_results = list(total_results.values())
        final_results.sort(key=lambda x: x.distance)

        k = min(k, len(final_results))

        return final_results[:k]

    def filter_retrieve(self, ticket: Ticket, k: int | None = None) -> List[RetrievalResult]:
        query = self._build_query(ticket)
        query_embedding = self._embed_query(query)

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
                chunk=result[0], distance=result[1], source="filter"))

        return filtered_results

    def semantic_retrieve(self, ticket: Ticket, k: int = 5) -> List[RetrievalResult]:
        if k <= 0:
            k = 5

        if k > len(self.chunks):
            k = len(self.chunks)

        query = self._build_query(ticket)
        query_embedding = self._embed_query(query)

        results = self.vectorstore.search_with_scores(
            query_embedding, k)

        semantic_results = []
        for result in results:
            semantic_results.append(RetrievalResult(
                chunk=result[0], distance=result[1], source="semantic"))

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

    def _build_query(self, ticket: Ticket) -> str:
        query = ticket.description
        return query

    def _embed_query(self, query: str):
        embedding = self.embedder.embed_texts([query])[0]
        return embedding
