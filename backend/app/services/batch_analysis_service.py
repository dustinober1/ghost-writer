"""
Batch analysis service for document similarity clustering and comparison.

Provides functionality for:
- Building pairwise similarity matrices from embeddings using cosine similarity
- Clustering documents based on similarity threshold (deterministic)
- Summarizing cluster statistics
"""

from typing import List, Dict, Optional
import numpy as np


def build_similarity_matrix(embeddings: List[List[float]]) -> List[List[float]]:
    """
    Build a symmetric similarity matrix using cosine similarity.

    Args:
        embeddings: List of embedding vectors (list of floats)

    Returns:
        A 2D list (similarity matrix) where:
        - matrix[i][j] is the cosine similarity between embeddings[i] and embeddings[j]
        - Diagonal elements are always 1.0 (self-similarity)
        - Matrix is symmetric (matrix[i][j] == matrix[j][i])
        - Values are in [-1, 1] range
        - Returns [] for empty input

    Examples:
        >>> build_similarity_matrix([[1.0, 0.0], [0.0, 1.0]])
        [[1.0, 0.0], [0.0, 1.0]]

        >>> build_similarity_matrix([[1.0, 0.0], [1.0, 0.0]])
        [[1.0, 1.0], [1.0, 1.0]]
    """
    if not embeddings:
        return []

    n = len(embeddings)
    # Convert to numpy array for efficient computation
    embeddings_array = np.array(embeddings, dtype=np.float64)

    # Compute cosine similarity matrix
    # Cosine similarity = (a . b) / (||a|| * ||b||)
    # Using numpy's efficient operations
    norms = np.linalg.norm(embeddings_array, axis=1)
    # Avoid division by zero for zero vectors
    norms = np.where(norms == 0, 1, norms)

    # Normalize embeddings
    normalized = embeddings_array / norms[:, np.newaxis]

    # Compute similarity matrix via dot product
    similarity_matrix = np.dot(normalized, normalized.T)

    # Ensure diagonal is exactly 1.0 (handles potential floating point issues)
    np.fill_diagonal(similarity_matrix, 1.0)

    # Convert to Python list of lists (JSON-serializable)
    return similarity_matrix.tolist()


def cluster_documents(
    embeddings: List[List[float]],
    threshold: float = 0.85
) -> List[Dict]:
    """
    Cluster documents based on pairwise similarity threshold.

    Uses deterministic single-pass clustering: documents with similarity
    >= threshold are grouped into the same cluster. Clustering is transitive
    (if A~B and B~C, then A,B,C are in same cluster).

    Args:
        embeddings: List of embedding vectors
        threshold: Minimum similarity for grouping (default 0.85)

    Returns:
        List of cluster dictionaries, each with:
        - cluster_id: int (sequential starting from 0)
        - document_ids: List[int] of document indices in this cluster
        - avg_similarity: float (average pairwise similarity within cluster)

    Examples:
        >>> cluster_documents([[1.0, 0.0], [0.0, 1.0]], threshold=0.5)
        [{'cluster_id': 0, 'document_ids': [0], 'avg_similarity': 1.0},
         {'cluster_id': 1, 'document_ids': [1], 'avg_similarity': 1.0}]

        >>> cluster_documents([[1.0, 0.0], [1.0, 0.0]], threshold=0.5)
        [{'cluster_id': 0, 'document_ids': [0, 1], 'avg_similarity': 1.0}]
    """
    if not embeddings:
        return []

    n = len(embeddings)

    # Build similarity matrix
    similarity_matrix = build_similarity_matrix(embeddings)

    # Union-Find data structure for efficient clustering
    parent = list(range(n))

    def find(x: int) -> int:
        """Find root of x with path compression."""
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: int, y: int) -> None:
        """Union the sets containing x and y."""
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            parent[root_y] = root_x

    # Group documents by threshold
    for i in range(n):
        for j in range(i + 1, n):
            if similarity_matrix[i][j] >= threshold:
                union(i, j)

    # Group documents by their root
    clusters_map: Dict[int, List[int]] = {}
    for doc_id in range(n):
        root = find(doc_id)
        if root not in clusters_map:
            clusters_map[root] = []
        clusters_map[root].append(doc_id)

    # Build result with cluster info
    result = []
    cluster_id = 0
    for root, document_ids in clusters_map.items():
        # Calculate average similarity within cluster
        cluster_similarities = []
        for i in document_ids:
            for j in document_ids:
                if i < j:  # Count each pair once
                    cluster_similarities.append(similarity_matrix[i][j])

        if cluster_similarities:
            avg_similarity = float(np.mean(cluster_similarities))
        else:
            avg_similarity = 1.0  # Single document cluster

        result.append({
            "cluster_id": cluster_id,
            "document_ids": document_ids,
            "avg_similarity": avg_similarity
        })
        cluster_id += 1

    # Sort by cluster_id for deterministic output
    result.sort(key=lambda x: x["cluster_id"])

    return result


def summarize_clusters(
    similarity_matrix: List[List[float]],
    clusters: List[Dict]
) -> List[Dict]:
    """
    Summarize cluster information with similarity matrix context.

    Args:
        similarity_matrix: The pairwise similarity matrix
        clusters: List of cluster dictionaries from cluster_documents()

    Returns:
        List of cluster summary dictionaries with same structure as input
        (acts as a pass-through with potential for future enhancement).

    Examples:
        >>> matrix = [[1.0, 0.5], [0.5, 1.0]]
        >>> clusters = [{"cluster_id": 0, "document_ids": [0, 1],
        ...             "avg_similarity": 0.5}]
        >>> summarize_clusters(matrix, clusters)
        [{'cluster_id': 0, 'document_ids': [0, 1], 'avg_similarity': 0.5}]
    """
    # Currently acts as a pass-through - structure allows for future
    # enhancements like computing additional statistics
    return clusters


class BatchAnalysisService:
    """
    Service for batch document analysis operations.

    Provides methods for similarity matrix generation, clustering,
    and cluster summarization for batch document analysis.
    """

    def __init__(self):
        """Initialize the batch analysis service."""
        pass

    def build_similarity_matrix(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Build a symmetric similarity matrix using cosine similarity.

        Args:
            embeddings: List of embedding vectors

        Returns:
            2D list similarity matrix with values in [-1, 1]
        """
        return build_similarity_matrix(embeddings)

    def cluster_documents(
        self,
        embeddings: List[List[float]],
        threshold: float = 0.85
    ) -> List[Dict]:
        """
        Cluster documents based on similarity threshold.

        Args:
            embeddings: List of embedding vectors
            threshold: Minimum similarity for clustering (default 0.85)

        Returns:
            List of cluster dictionaries with cluster_id, document_ids,
            and avg_similarity
        """
        return cluster_documents(embeddings, threshold)

    def summarize_clusters(
        self,
        similarity_matrix: List[List[float]],
        clusters: List[Dict]
    ) -> List[Dict]:
        """
        Summarize cluster information.

        Args:
            similarity_matrix: Pairwise similarity matrix
            clusters: List of cluster dictionaries

        Returns:
            List of cluster summary dictionaries
        """
        return summarize_clusters(similarity_matrix, clusters)


# Global service instance
_batch_analysis_service = None


def get_batch_analysis_service() -> BatchAnalysisService:
    """
    Get or create the global batch analysis service instance.

    Returns:
        The singleton BatchAnalysisService instance
    """
    global _batch_analysis_service
    if _batch_analysis_service is None:
        _batch_analysis_service = BatchAnalysisService()
    return _batch_analysis_service
