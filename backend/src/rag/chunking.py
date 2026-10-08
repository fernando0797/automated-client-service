from __future__ import annotations
from src.core.models import KnowledgeChunk, KnowledgeDocument


class Chunker:
    def __init__(
        self,
        documents: list[KnowledgeDocument],
        chunk_size: int = 225,
        chunk_overlap: int = 35,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be between zero and chunk_size")

        self.documents = documents
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_all_documents(self) -> list[KnowledgeChunk]:
        knowledge_chunks_global = []

        for document in self.documents:
            knowledge_chunks = self._chunk_knowledge_document(document)
            knowledge_chunks_global.extend(knowledge_chunks)

        return knowledge_chunks_global

    def _chunk_knowledge_document(
        self,
        knowledgedocument: KnowledgeDocument
    ) -> list[KnowledgeChunk]:
        knowledge_chunks = []
        content = knowledgedocument.content
        metadata = knowledgedocument.metadata
        doc_id = knowledgedocument.doc_id
        chunks = self._split_text(content)

        for index, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}__chunk_{index}"
            parent_doc_id = doc_id
            chunk_content = chunk
            enriched_metadata = self._extract_metadata(metadata, index)

            knowledgechunk = KnowledgeChunk(
                chunk_id=chunk_id,
                parent_doc_id=parent_doc_id,
                content=chunk_content,
                metadata=enriched_metadata
            )

            knowledge_chunks.append(knowledgechunk)

        return knowledge_chunks

    def _split_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []

        step = self.chunk_size - self.chunk_overlap
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += step

        return chunks

    def _extract_metadata(self, metadata: dict, index: int) -> dict:
        enriched_metadata = {
            key: value
            for key, value in metadata.items()
            if key != "filename"
        }

        enriched_metadata["chunk_index"] = index
        return enriched_metadata
