"""Tests for batch analysis service - similarity matrix and clustering."""

import numpy as np
import pytest

from app.services.batch_analysis_service import (
    BatchAnalysisService,
    build_similarity_matrix,
    cluster_documents,
    summarize_clusters,
)


class TestBuildSimilarityMatrix:
    """Tests for build_similarity_matrix function."""

    def test_empty_embeddings_returns_empty_matrix(self):
        """Empty input should return empty matrix."""
        result = build_similarity_matrix([])
        assert result == []

    def test_single_embedding_returns_1x1_matrix(self):
        """Single embedding should return 1x1 matrix with 1.0."""
        embeddings = [[1.0, 0.0, 0.0]]
        result = build_similarity_matrix(embeddings)
        assert result == [[1.0]]

    def test_identical_vectors_returns_similarity_1(self):
        """Two identical vectors should have similarity 1.0."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        result = build_similarity_matrix(embeddings)
        assert len(result) == 2
        assert len(result[0]) == 2
        assert result[0][0] == 1.0  # diagonal
        assert result[1][1] == 1.0  # diagonal
        assert result[0][1] == 1.0  # identical vectors
        assert result[1][0] == 1.0  # symmetric

    def test_orthogonal_vectors_returns_similarity_0(self):
        """Orthogonal vectors should have similarity near 0.0."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
        result = build_similarity_matrix(embeddings)
        assert len(result) == 2
        assert result[0][0] == 1.0  # diagonal
        assert result[1][1] == 1.0  # diagonal
        assert abs(result[0][1]) < 0.01  # orthogonal
        assert abs(result[1][0]) < 0.01  # symmetric

    def test_opposite_vectors_returns_similarity_neg1(self):
        """Opposite vectors should have similarity -1.0."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
        ]
        result = build_similarity_matrix(embeddings)
        assert len(result) == 2
        assert result[0][0] == 1.0  # diagonal
        assert result[1][1] == 1.0  # diagonal
        assert result[0][1] == -1.0  # opposite
        assert result[1][0] == -1.0  # symmetric

    def test_symmetric_matrix(self):
        """Similarity matrix should be symmetric."""
        embeddings = [
            [1.0, 0.5, 0.3],
            [0.2, 0.8, 0.1],
            [0.9, 0.1, 0.4],
        ]
        result = build_similarity_matrix(embeddings)
        for i in range(len(result)):
            for j in range(len(result)):
                assert result[i][j] == result[j][i]

    def test_diagonal_is_1(self):
        """Diagonal elements should always be 1.0."""
        embeddings = [
            [1.0, 0.5, 0.3],
            [0.2, 0.8, 0.1],
            [0.9, 0.1, 0.4],
            [0.3, 0.3, 0.3],
        ]
        result = build_similarity_matrix(embeddings)
        for i in range(len(result)):
            assert result[i][i] == 1.0

    def test_cosine_similarity_values_in_range(self):
        """All values should be in [-1, 1] range."""
        embeddings = [
            [1.0, 0.5, 0.3],
            [0.2, 0.8, 0.1],
            [0.9, 0.1, 0.4],
        ]
        result = build_similarity_matrix(embeddings)
        for row in result:
            for val in row:
                assert -1.0 <= val <= 1.0

    def test_json_serializable_output(self):
        """Output should be JSON-serializable (no numpy types)."""
        embeddings = [
            [1.0, 0.5, 0.3],
            [0.2, 0.8, 0.1],
        ]
        result = build_similarity_matrix(embeddings)
        import json
        json_str = json.dumps(result)
        assert json_str is not None

    def test_realistic_embeddings(self):
        """Test with realistic embedding values."""
        # Simulated normalized embeddings (real embeddings are unit vectors)
        # All properly normalized to unit length
        embeddings = [
            [0.57735, 0.57735, 0.57735],  # normalized [1,1,1]
            [0.70711, 0.70711, 0.0],      # normalized [1,1,0]
            [0.0, 0.0, 1.0],              # normalized [0,0,1]
        ]
        result = build_similarity_matrix(embeddings)
        assert len(result) == 3
        # First two: dot = 0.57735*0.70711 + 0.57735*0.70711 + 0.57735*0 = ~0.816
        # (approx 35 degrees between them)
        assert abs(result[0][1] - 0.816) < 0.01
        # First and third: dot = 0.57735 (approx 55 degrees)
        assert abs(result[0][2] - 0.577) < 0.01
        # Second and third: orthogonal (dot = 0)
        assert abs(result[1][2]) < 0.01

    def test_different_dimensions(self):
        """Handle different embedding dimensions."""
        # 2D embeddings
        embeddings_2d = [[1.0, 0.0], [0.0, 1.0]]
        result = build_similarity_matrix(embeddings_2d)
        assert len(result) == 2
        assert abs(result[0][1]) < 0.01

        # 128D embeddings (simulated)
        embeddings_128d = [[1.0] * 64 + [0.0] * 64, [0.0] * 64 + [1.0] * 64]
        result = build_similarity_matrix(embeddings_128d)
        assert len(result) == 2
        assert abs(result[0][1]) < 0.01


class TestClusterDocuments:
    """Tests for cluster_documents function."""

    def test_empty_embeddings_returns_empty_clusters(self):
        """Empty input should return empty clusters."""
        result = cluster_documents([])
        assert result == []

    def test_single_document_returns_single_cluster(self):
        """Single document should form its own cluster."""
        embeddings = [[1.0, 0.0, 0.0]]
        result = cluster_documents(embeddings)
        assert len(result) == 1
        assert result[0]["cluster_id"] == 0
        assert result[0]["document_ids"] == [0]

    def test_identical_documents_same_cluster(self):
        """Identical documents should be in the same cluster."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        result = cluster_documents(embeddings)
        assert len(result) == 1
        assert result[0]["cluster_id"] == 0
        assert set(result[0]["document_ids"]) == {0, 1, 2}
        assert result[0]["avg_similarity"] == 1.0

    def test_orthogonal_documents_separate_clusters(self):
        """Orthogonal documents should form separate clusters."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
        result = cluster_documents(embeddings, threshold=0.85)
        assert len(result) == 2
        cluster_ids = {c["cluster_id"] for c in result}
        assert cluster_ids == {0, 1}

    def test_custom_threshold_respected(self):
        """Custom threshold should be respected."""
        # Vectors at 60 degrees, cos(60) = 0.5
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.5, 0.866, 0.0],  # 60 degrees from first
        ]
        # With threshold 0.4, should cluster together
        result = cluster_documents(embeddings, threshold=0.4)
        assert len(result) == 1

        # With threshold 0.6, should be separate
        result = cluster_documents(embeddings, threshold=0.6)
        assert len(result) == 2

    def test_cluster_id_sequence(self):
        """Cluster IDs should be sequential starting from 0."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        result = cluster_documents(embeddings, threshold=0.5)
        cluster_ids = [c["cluster_id"] for c in result]
        assert sorted(cluster_ids) == list(range(len(result)))

    def test_transitive_clustering(self):
        """If A~B and B~C, then A, B, C should be in same cluster."""
        # Create vectors where:
        # v0 and v1 are similar (above threshold)
        # v1 and v2 are similar (above threshold)
        # v0 and v2 are below threshold
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],  # similar to v0
            [0.8, 0.2, 0.0],  # similar to v1, less to v0
        ]
        result = cluster_documents(embeddings, threshold=0.85)
        # All should be in same cluster due to transitivity
        assert len(result) == 1
        assert set(result[0]["document_ids"]) == {0, 1, 2}

    def test_multiple_clusters_detected(self):
        """Detect multiple natural clusters."""
        # Two distinct groups
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.95, 0.05],
        ]
        result = cluster_documents(embeddings, threshold=0.85)
        assert len(result) == 2
        # First cluster has docs 0, 1
        cluster_0 = next(c for c in result if c["cluster_id"] == 0)
        assert set(cluster_0["document_ids"]) == {0, 1}
        # Second cluster has docs 2, 3
        cluster_1 = next(c for c in result if c["cluster_id"] == 1)
        assert set(cluster_1["document_ids"]) == {2, 3}

    def test_avg_similarity_calculation(self):
        """Average similarity should be calculated correctly."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        result = cluster_documents(embeddings)
        # For identical vectors, all pairs are 1.0
        # avg_similarity should be 1.0
        assert result[0]["avg_similarity"] == 1.0

    def test_json_serializable_output(self):
        """Output should be JSON-serializable."""
        embeddings = [[1.0, 0.5, 0.3], [0.2, 0.8, 0.1]]
        result = cluster_documents(embeddings)
        import json
        json_str = json.dumps(result)
        assert json_str is not None

    def test_threshold_0_all_same_cluster(self):
        """With threshold 0, all documents in same cluster."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        result = cluster_documents(embeddings, threshold=0.0)
        assert len(result) == 1
        assert set(result[0]["document_ids"]) == {0, 1, 2}

    def test_threshold_1_all_separate_clusters(self):
        """With threshold 1, all documents in separate clusters."""
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],  # identical but threshold prevents grouping
        ]
        result = cluster_documents(embeddings, threshold=1.01)  # above max
        assert len(result) == 2

    def test_deterministic_output(self):
        """Same input should produce same output."""
        embeddings = [
            [1.0, 0.5, 0.3],
            [0.2, 0.8, 0.1],
            [0.9, 0.1, 0.4],
        ]
        result1 = cluster_documents(embeddings, threshold=0.7)
        result2 = cluster_documents(embeddings, threshold=0.7)
        assert result1 == result2


class TestSummarizeClusters:
    """Tests for summarize_clusters function."""

    def test_empty_matrix_and_clusters(self):
        """Empty input should return empty summary."""
        result = summarize_clusters([], [])
        assert result == []

    def test_single_cluster_summary(self):
        """Single cluster should return single summary."""
        similarity_matrix = [[1.0]]
        clusters = [{"cluster_id": 0, "document_ids": [0], "avg_similarity": 1.0}]
        result = summarize_clusters(similarity_matrix, clusters)
        assert len(result) == 1
        assert result[0]["cluster_id"] == 0
        assert result[0]["document_ids"] == [0]

    def test_summary_preserves_cluster_structure(self):
        """Summary should preserve cluster structure."""
        similarity_matrix = [
            [1.0, 0.9, 0.1, 0.1],
            [0.9, 1.0, 0.1, 0.1],
            [0.1, 0.1, 1.0, 0.9],
            [0.1, 0.1, 0.9, 1.0],
        ]
        clusters = [
            {"cluster_id": 0, "document_ids": [0, 1], "avg_similarity": 0.9},
            {"cluster_id": 1, "document_ids": [2, 3], "avg_similarity": 0.9},
        ]
        result = summarize_clusters(similarity_matrix, clusters)
        assert len(result) == 2
        assert result[0]["document_ids"] == [0, 1]
        assert result[1]["document_ids"] == [2, 3]

    def test_json_serializable_output(self):
        """Output should be JSON-serializable."""
        similarity_matrix = [[1.0, 0.5], [0.5, 1.0]]
        clusters = [{"cluster_id": 0, "document_ids": [0, 1], "avg_similarity": 0.5}]
        result = summarize_clusters(similarity_matrix, clusters)
        import json
        json_str = json.dumps(result)
        assert json_str is not None


class TestBatchAnalysisService:
    """Tests for BatchAnalysisService class."""

    def test_service_instantiation(self):
        """Service should be instantiable."""
        service = BatchAnalysisService()
        assert service is not None

    def test_build_similarity_matrix_method(self):
        """Service method should delegate to function."""
        service = BatchAnalysisService()
        embeddings = [[1.0, 0.0], [0.0, 1.0]]
        result = service.build_similarity_matrix(embeddings)
        assert len(result) == 2

    def test_cluster_documents_method(self):
        """Service method should delegate to function."""
        service = BatchAnalysisService()
        embeddings = [[1.0, 0.0], [0.0, 1.0]]
        result = service.cluster_documents(embeddings, threshold=0.85)
        assert len(result) == 2

    def test_summarize_clusters_method(self):
        """Service method should delegate to function."""
        service = BatchAnalysisService()
        matrix = [[1.0]]
        clusters = [{"cluster_id": 0, "document_ids": [0], "avg_similarity": 1.0}]
        result = service.summarize_clusters(matrix, clusters)
        assert len(result) == 1
