import json
import random
import math
from typing import List, Dict, Any


def load_articles(path: str) -> List[Dict[str, Any]]:
    """Load articles from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["articles"]  # list of {"id": ..., "categories": [...]}


# ---- basic k-means implementation ---- #

def _euclidean(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _mean_vector(vectors: List[List[float]]) -> List[float]:
    n = len(vectors)
    if n == 0:
        return []
    dim = len(vectors[0])
    return [sum(vec[i] for vec in vectors) / n for i in range(dim)]


def _kmeans(vectors: List[List[float]], k: int, max_iters: int = 100) -> List[int]:
    """
    Very simple k-means: returns a label (0..k-1) for each vector.
    """
    n = len(vectors)
    if k > n:
        raise ValueError("k (num groups) cannot be larger than number of vectors")

    # 1) init centroids by sampling k random points
    indices = random.sample(range(n), k)
    centroids = [vectors[i][:] for i in indices]

    labels = [0] * n

    for _ in range(max_iters):
        # 2) assign step
        new_labels = []
        for vec in vectors:
            dists = [_euclidean(vec, c) for c in centroids]
            new_labels.append(dists.index(min(dists)))

        # check convergence
        if new_labels == labels:
            break
        labels = new_labels

        # 3) update step
        for cluster_id in range(k):
            cluster_vecs = [v for v, lab in zip(vectors, labels) if lab == cluster_id]
            if cluster_vecs:  # avoid empty cluster
                centroids[cluster_id] = _mean_vector(cluster_vecs)

    return labels


# ---- public function you asked for ---- #

def group_articles_by_categories(articles: List[Dict[str, Any]], num: int) -> List[List[int]]:
    """
    Cluster articles into `num` groups according to their category vectors.

    :param articles: list of {"id": ..., "categories": [...]}
    :param num: number of groups (clusters) to return
    :return: list of groups, each group is a list of article IDs
    """
    if num <= 0:
        raise ValueError("num must be positive")

    vectors = [a["categories"] for a in articles]
    ids = [a["id"] for a in articles]

    labels = _kmeans(vectors, num)
    
    clusters: Dict[int, List[int]] = {}
    for article_id, label in zip(ids, labels):
        clusters.setdefault(label, []).append(article_id)

    # return just the groups of IDs (order of groups is arbitrary)
    return list(clusters.values())


# ---- example usage ---- #

if __name__ == "__main__":
    articles = load_articles("../experiments/articles.json")
    groups = group_articles_by_categories(articles, num=5)  # e.g. 10 groups
    for i, g in enumerate(groups, start=1):
        print(f"Group {i}: {g}")
