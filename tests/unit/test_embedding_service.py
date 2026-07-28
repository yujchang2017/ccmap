"""Offline unit tests for EmbeddingService (no API key, no network)."""
import numpy as np

from app.services.embedding_service import EmbeddingService


def make_service(dim=4):
    # No API key: the service must degrade to zero vectors without network access.
    return EmbeddingService(api_key=None, embedding_dim=dim)


class TestOfflineDegradation:
    def test_single_embedding_returns_zero_without_key(self):
        svc = make_service()
        emb = svc.get_openai_embedding("some text")
        assert emb.shape == (4,)
        assert np.all(emb == 0)

    def test_batch_embeddings_return_zeros_without_key(self):
        svc = make_service()
        embs = svc.get_openai_embeddings(["a", "b", "c"])
        assert embs.shape == (3, 4)
        assert np.all(embs == 0)


class TestSanitizeText:
    def test_truncates_and_strips(self):
        svc = make_service()
        assert svc._sanitize_text("  hi  ") == "hi"
        assert len(svc._sanitize_text("x" * 10000)) == 6000
        assert svc._sanitize_text(None) == ""
        assert svc._sanitize_text("a\x00b") == "ab"


class TestCalculateSimilarities:
    def test_parallel_and_orthogonal_vectors(self):
        svc = make_service(dim=3)
        query = np.array([1.0, 0.0, 0.0])
        targets = np.array([
            [2.0, 0.0, 0.0],   # parallel → 1.0
            [0.0, 5.0, 0.0],   # orthogonal → 0.0
            [-1.0, 0.0, 0.0],  # opposite → -1.0
        ])
        sims = svc.calculate_similarities(query, targets)
        assert np.allclose(sims, [1.0, 0.0, -1.0], atol=1e-6)

    def test_zero_query_returns_zeros(self):
        svc = make_service(dim=3)
        sims = svc.calculate_similarities(np.zeros(3), np.eye(3))
        assert np.all(sims == 0)

    def test_zero_target_rows_are_guarded(self):
        svc = make_service(dim=3)
        targets = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        sims = svc.calculate_similarities(np.array([1.0, 0.0, 0.0]), targets)
        assert sims[0] == 0.0
        assert abs(sims[1] - 1.0) < 1e-6


class TestRanking:
    def test_top_k_ordering_by_precomputed_embedding(self):
        svc = make_service(dim=3)
        texts = ["far", "near", "mid"]
        embeddings = np.array([
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.7, 0.7, 0.0],
        ])
        query = np.array([1.0, 0.0, 0.0])
        result = svc.find_most_similar_keyideas_by_embedding(query, texts, embeddings, top_k=2)
        assert [t for t, _ in result] == ["near", "mid"]
        assert result[0][1] > result[1][1]

    def test_zero_query_embedding_returns_empty(self):
        svc = make_service(dim=3)
        result = svc.find_most_similar_keyideas_by_embedding(
            np.zeros(3), ["a"], np.eye(3)[:1], top_k=5
        )
        assert result == []
