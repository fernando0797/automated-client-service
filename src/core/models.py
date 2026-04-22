from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class KnowledgeDocument:
    doc_id: str
    content: str
    metadata: Dict[str, Any]

    @property
    def type(self) -> str:
        return self.metadata["type"]


@dataclass
class KnowledgeChunk:
    chunk_id: str
    parent_doc_id: str
    content: str
    metadata: Dict[str, Any]

    @property
    def type(self) -> str:
        return self.metadata["type"]


@dataclass
class RetrievalResult:
    chunk: KnowledgeChunk
    distance: float
    source: str
