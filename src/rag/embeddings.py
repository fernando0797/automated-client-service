from sentence_transformers import SentenceTransformer
from typing import List

from src.core.models import KnowledgeChunk


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]):
        if not texts:
            return []

        embeddings = self.model.encode(texts)
        return embeddings

    def embed_chunks(self, chunks: List[KnowledgeChunk]):
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(texts)
        return embeddings
