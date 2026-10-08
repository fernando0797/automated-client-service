from typing import List, Tuple

from src.core.models import KnowledgeChunk


class VectorStore:
    def __init__(self):
        self.index: list[list[float]] | None = None
        self.chunks: List[KnowledgeChunk] = []
        self.dimension: int | None = None

    def build_index(self, embeddings, chunks: List[KnowledgeChunk]) -> None:
        if len(embeddings) == 0:
            raise ValueError("Embeddings list cannot be empty.")

        if len(embeddings) != len(chunks):
            raise ValueError(
                "The number of embeddings must match the number of chunks."
            )

        if any(not isinstance(embedding, (list, tuple)) for embedding in embeddings):
            raise ValueError("Embeddings must be a 2D array.")

        dimension = len(embeddings[0])
        if dimension == 0 or any(len(embedding) != dimension for embedding in embeddings):
            raise ValueError("Embeddings must have the same non-zero dimension.")

        self.dimension = dimension
        self.index = [list(map(float, embedding)) for embedding in embeddings]

        self.chunks = chunks

    def search(self, query_embedding, k: int = 3) -> List[KnowledgeChunk]:
        if self.index is None:
            raise ValueError("The vector index has not been built yet.")

        return [self.chunks[index] for index, _ in self._nearest(query_embedding, k)]

    def search_with_scores(self, query_embedding, k: int = 3) -> List[Tuple[KnowledgeChunk, float]]:
        if self.index is None:
            raise ValueError("The vector index has not been built yet.")

        return [
            (self.chunks[index], distance)
            for index, distance in self._nearest(query_embedding, k)
        ]

    def _nearest(self, query_embedding, k: int) -> list[tuple[int, float]]:
        if self.index is None or self.dimension is None:
            raise ValueError("The vector index has not been built yet.")

        query = list(map(float, query_embedding))
        if len(query) != self.dimension:
            raise ValueError(
                "Query embedding dimension does not match index dimension.")

        distances = [
            (
                index,
                float(
                    sum(
                        (value - query_value) ** 2
                        for value, query_value in zip(vector, query)
                    )
                ),
            )
            for index, vector in enumerate(self.index)
        ]
        distances.sort(key=lambda item: item[1])
        return distances[:max(k, 0)]
