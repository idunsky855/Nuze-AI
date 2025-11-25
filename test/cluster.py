import json
import math
import random
from typing import List, Dict, Any
from sklearn.cluster import KMeans

random.seed(42)


def load_articles(path: str) -> List[Dict[str, Any]]:
    """Load articles from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["articles"]


def group_articles_by_size(
    articles: List[Dict[str, Any]],
    num: int,
    random_state: int = 0
) -> List[List[int]]:
    """
    Group articles into chunks of size `num`, ensuring that articles
    inside each group are as similar as possible (via clustering).

    :param num: number of articles per group
    :return: list of groups, each group is a list of article IDs
    """
    if num <= 0:
        raise ValueError("num must be positive")

    vectors = [a["categories"] for a in articles]
    ids = [a["id"] for a in articles]

    total = len(articles)

    # how many clusters do we need?
    k = math.ceil(total / num)

    kmeans = KMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=10
    )

    labels = kmeans.fit_predict(vectors)

    # group by cluster similarity
    clusters: Dict[int, List[int]] = {}
    for article_id, label in zip(ids, labels):
        clusters.setdefault(label, []).append(article_id)

    final_groups: List[List[int]] = []

    # now break each cluster into chunks of size `num`
    for group in clusters.values():
        for i in range(0, len(group), num):
            final_groups.append(group[i:i + num])

    return final_groups


# ---- example usage ---- #

if __name__ == "__main__":
    articles = load_articles("../experiments/articles.json")

    groups = group_articles_by_size(articles, num=5)

    for i, g in enumerate(groups, start=1):
        print(f"Group {i}: {g}")
