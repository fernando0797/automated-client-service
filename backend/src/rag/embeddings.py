from typing import Protocol

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.core.models import KnowledgeChunk


class EmbeddingModel(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class Embedder:
    def __init__(
        self,
        model_name: str = "gemini-embedding-001",
        model: EmbeddingModel | None = None,
    ) -> None:
        self.model = model or GoogleGenerativeAIEmbeddings(model=model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)

    def embed_chunks(self, chunks: list[KnowledgeChunk]) -> list[list[float]]:
        texts = [chunk.content for chunk in chunks]
        return self.embed_texts(texts)
