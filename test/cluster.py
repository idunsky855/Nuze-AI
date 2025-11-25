import json
import math
from typing import List, Dict, Any
from sklearn.cluster import KMeans


def load_articles(path: str) -> List[Dict[str, Any]]:
    """Load articles from a JSON file.

    Expected JSON structure:
    {
        "articles": [
            {
                "id": ...,
                "categories": [...]
            },
            ...
        ]
    }
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["articles"]


def group_articles_by_size(
    articles: List[Dict[str, Any]],
    num: int,
    random_state: int = 42
) -> List[List[int]]:
    """
    Group articles into chunks of size `num`, ensuring that articles
    inside each group are as similar as possible (via clustering).

    - `num` is the number of articles per group (except possibly the last ones).
    - Uses sklearn KMeans to cluster first, then chunks each cluster.

    :param articles: list of {"id": ..., "categories": [...]}
    :param num: number of articles per group
    :param random_state: random seed for KMeans
    :return: list of groups, each group is a list of article IDs
    """
    if num <= 0:
        raise ValueError("num must be positive")

    total = len(articles)
    if total == 0:
        return []

    vectors = [a["categories"] for a in articles]
    ids = [a["id"] for a in articles]

    # how many clusters do we need?
    k = math.ceil(total / num)

    kmeans = KMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=10
    )

    labels = kmeans.fit_predict(vectors)

    # group by cluster similarity (label -> list of article ids)
    clusters: Dict[int, List[int]] = {}
    for article_id, label in zip(ids, labels):
        clusters.setdefault(label, []).append(article_id)

    final_groups: List[List[int]] = []

    # break each cluster into chunks of size `num`
    # sort labels to make output deterministic
    for label in sorted(clusters.keys()):
        group = clusters[label]
        for i in range(0, len(group), num):
            final_groups.append(group[i:i + num])

    return final_groups


# ---- example usage ---- #

if __name__ == "__main__":
    articles = load_articles("../experiments/articles.json")

    # num = number of articles per group
    groups = group_articles_by_size(articles, num=5)

    for i, g in enumerate(groups, start=1):
        print(f"Group {i}: {g}")
