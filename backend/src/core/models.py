from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass
class KnowledgeDocument:
    doc_id: str
    content: str
    metadata: dict[str, Any]

    @property
    def type(self) -> str:
        return self.metadata["type"]


@dataclass
class KnowledgeChunk:
    chunk_id: str
    parent_doc_id: str
    content: str
    metadata: dict[str, Any]

    @property
    def type(self) -> str:
        return self.metadata["type"]


class RetrievalResult(BaseModel):
    chunk: KnowledgeChunk
    distance: float
    source: str
