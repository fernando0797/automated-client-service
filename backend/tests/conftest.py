import pytest


class FakeEmbeddingModel:
    """Small deterministic embedding model for tests without external API calls."""

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = [0.0] * 8
        for word in text.lower().split():
            bucket = sum(map(ord, word)) % len(vector)
            vector[bucket] += 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@pytest.fixture(scope="module")
def fake_embedding_model() -> FakeEmbeddingModel:
    return FakeEmbeddingModel()
