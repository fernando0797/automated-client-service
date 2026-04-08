from __future__ import annotations
from langchain_text_splitters import TokenTextSplitter

from src.core.models import KnowledgeChunk, KnowledgeDocument
from src.rag.loader import KnowledgeLoader
from src.core.config import KNOWLEDGE_PATH


class Chunker:
    def __init__(self, documents: list[KnowledgeDocument]):
        self.documents = documents
        self.text_splitter = TokenTextSplitter(
            chunk_size=225,
            chunk_overlap=35
        )

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
        chunks = self.text_splitter.split_text(content)

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

    def _extract_metadata(self, metadata: dict, index: int) -> dict:
        enriched_metadata = {
            key: value
            for key, value in metadata.items()
            if key != "filename"
        }

        enriched_metadata["chunk_index"] = index
        return enriched_metadata
