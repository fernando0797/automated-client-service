import faiss
import numpy as np
from typing import List, Tuple

from src.core.models import KnowledgeChunk


class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks: List[KnowledgeChunk] = []
        self.dimension: int | None = None

    def build_index(self, embeddings, chunks: List[KnowledgeChunk]) -> None:
        if len(embeddings) == 0:
            raise ValueError("Embeddings list cannot be empty.")

        if len(embeddings) != len(chunks):
            raise ValueError(
                "The number of embeddings must match the number of chunks."
            )

        embeddings_array = np.array(embeddings, dtype="float32")

        if embeddings_array.ndim != 2:
            raise ValueError("Embeddings must be a 2D array.")

        self.dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings_array)

        self.chunks = chunks

    def search(self, query_embedding, k: int = 3) -> List[KnowledgeChunk]:
        if self.index is None:
            raise ValueError("The FAISS index has not been built yet.")

        query_array = np.array([query_embedding], dtype="float32")

        if query_array.ndim != 2:
            raise ValueError("Query embedding (array) must be a 2D array.")

        if query_array.shape[1] != self.dimension:
            raise ValueError(
                "Query embedding dimension does not match index dimension.")

        distances, indices = self.index.search(query_array, k)

        results = []
        for idx in indices[0]:
            if idx != -1:
                results.append(self.chunks[idx])

        return results

    def search_with_scores(self, query_embedding, k: int = 3) -> List[Tuple[KnowledgeChunk, float]]:
        if self.index is None:
            raise ValueError("The FAISS index has not been built yet.")

        query_array = np.array([query_embedding], dtype="float32")

        if query_array.ndim != 2:
            raise ValueError("Query embedding (array) must be a 2D array.")

        if query_array.shape[1] != self.dimension:
            raise ValueError(
                "Query embedding dimension does not match index dimension.")

        distances, indices = self.index.search(query_array, k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1:
                results.append((self.chunks[idx], float(distance)))

        return results
