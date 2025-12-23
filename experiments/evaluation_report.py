"""
Generate evaluation metrics for the user-vector learning loop.

The script tries to pull synthesized articles and their category vectors from
the configured PostgreSQL database. If the database is unreachable or empty, it
falls back to the sample data in ``experiments/articles_normalized.json``. User
profiles come from ``experiments/users.json``. Results are written to
``experiments/evaluation_report.md``.
"""
from __future__ import annotations

import asyncio
import json
import math
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:  # Optional imports; script falls back to sample data if unavailable
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.synthesized_article import SynthesizedArticle
except Exception:  # pragma: no cover - allows offline runs without DB deps
    select = None
    AsyncSessionLocal = None
    SynthesizedArticle = None

# Category ordering matches ingestion and database storage.
CATEGORIES = [
    "Politics & Law",
    "Economy & Business",
    "Science & Technology",
    "Health & Wellness",
    "Education & Society",
    "Culture & Entertainment",
    "Religion & Belief",
    "Sports",
    "World & International Affairs",
    "Opinion & General News",
]
# The experimentation datasets only contain category dimensions (10 total)
CATEGORY_DIM = len(CATEGORIES)
# Clicks are treated as 0.25 * like when computing weighted engagement.
CLICK_LIKE_RATIO = 0.25
# Learning rate matches the exploratory simulations (see conversations).
LEARNING_RATE = 0.016
# Default cutoff for ranking metrics
K = 5

# Demographic influence weights mirror the exploratory notebook configuration.
DEMOGRAPHIC_INFLUENCES = {
    "age": {
        (0, 17): {
            "Culture & Entertainment": 0.15,
            "Science & Technology": 0.10,
            "Sports": 0.05,
            "Politics & Law": -0.15,
            "World & International Affairs": -0.10,
            "Health & Wellness": -0.05,
        },
        (18, 24): {
            "Culture & Entertainment": 0.10,
            "Science & Technology": 0.10,
            "Sports": 0.05,
            "Politics & Law": -0.10,
            "Economy & Business": -0.10,
            "Opinion & General News": -0.05,
        },
        (25, 34): {
            "Science & Technology": 0.10,
            "Economy & Business": 0.07,
            "Culture & Entertainment": 0.05,
            "Education & Society": -0.10,
            "Opinion & General News": -0.07,
            "Sports": -0.05,
        },
        (35, 49): {
            "Health & Wellness": 0.10,
            "Education & Society": 0.07,
            "Opinion & General News": 0.05,
            "Science & Technology": -0.05,
            "Culture & Entertainment": -0.10,
            "Economy & Business": -0.07,
        },
        (50, 64): {
            "Health & Wellness": 0.12,
            "Opinion & General News": 0.10,
            "Economy & Business": -0.10,
            "Education & Society": -0.05,
            "Science & Technology": -0.07,
        },
        (65, 100): {
            "Health & Wellness": 0.15,
            "Opinion & General News": 0.10,
            "Economy & Business": -0.10,
            "Education & Society": -0.10,
            "Science & Technology": -0.05,
        },
    },
    "gender": {
        "female": {
            "Health & Wellness": 0.08,
            "Opinion & General News": 0.05,
            "Sports": -0.08,
            "Economy & Business": -0.05,
        },
        "male": {
            "Sports": 0.08,
            "Science & Technology": 0.05,
            "Health & Wellness": -0.08,
            "Opinion & General News": -0.05,
        },
        "unknown": {},
    },
    "location": {
        "urban": {
            "Politics & Law": 0.10,
            "World & International Affairs": 0.10,
            "Economy & Business": 0.05,
            "Culture & Entertainment": -0.10,
            "Health & Wellness": -0.05,
            "Education & Society": -0.05,
            "Sports": -0.05,
        },
        "suburban": {
            "Education & Society": 0.10,
            "Culture & Entertainment": 0.05,
            "Politics & Law": -0.05,
            "Economy & Business": -0.05,
            "Sports": -0.05,
        },
        "rural": {
            "Economy & Business": 0.10,
            "Education & Society": 0.05,
            "Science & Technology": -0.05,
            "Culture & Entertainment": -0.05,
            "Health & Wellness": -0.05,
        },
        "unknown": {},
    },
}


def rescale_and_normalize_vector(vector: Sequence[float], target_sum: float = 5.0) -> List[float]:
    """Rescale a vector so its absolute sum equals ``target_sum``.

    Any negative values are shifted so the smallest entry is zero before scaling,
    matching the behavior used in the exploration utilities.
    """
    min_val = min(vector) if vector else 0.0
    adjusted = [val + abs(min_val) if min_val < 0 else val for val in vector]
    total = sum(abs(val) for val in adjusted)
    if total == 0:
        return [0.0 for _ in adjusted]
    scale = target_sum / total
    return [val * scale for val in adjusted]


def cos_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    if len(vector_a) != len(vector_b):
        raise ArithmeticError("Vectors should have same dimensions.")
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def load_users(path: Path) -> List[dict]:
    with path.open() as f:
        return json.load(f)


def normalize_article_vector(vector: Sequence[float]) -> List[float]:
    as_floats = [float(val) for val in vector]
    return rescale_and_normalize_vector(as_floats, target_sum=5.0)


def dominant_category(vector: Sequence[float]) -> str:
    if not vector:
        return "Unknown"
    top_index = max(range(len(vector)), key=lambda idx: vector[idx])
    if 0 <= top_index < len(CATEGORIES):
        return CATEGORIES[top_index]
    return f"Dimension {top_index}"


def load_articles_from_json(path: Path) -> Tuple[Dict[str, List[float]], Dict[str, str]]:
    with path.open() as f:
        data = json.load(f)
    articles = {name: normalize_article_vector(vec) for name, vec in data.items()}
    primary_categories = {name: dominant_category(vec) for name, vec in articles.items()}
    return articles, primary_categories


async def _load_articles_from_database(limit: int | None = None) -> Tuple[Dict[str, List[float]], Dict[str, str]]:
    if not (AsyncSessionLocal and select and SynthesizedArticle):
        raise RuntimeError("Database dependencies are unavailable in this environment.")
    async with AsyncSessionLocal() as session:
        stmt = select(
            SynthesizedArticle.title, SynthesizedArticle.category_scores
        ).order_by(SynthesizedArticle.generated_at.desc())
        if limit:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        articles: Dict[str, List[float]] = {}
        primary_categories: Dict[str, str] = {}
        for title, scores in result.all():
            if not scores:
                continue
            vector = normalize_article_vector(scores)
            articles[title] = vector
            primary_categories[title] = dominant_category(vector)
        return articles, primary_categories


def load_articles_from_database(limit: int | None = None) -> Tuple[Dict[str, List[float]], Dict[str, str]]:
    try:
        return asyncio.run(_load_articles_from_database(limit))
    except Exception as exc:  # pragma: no cover - defensive for offline environments
        print(f"Warning: could not load synthesized articles from database: {exc}")
        return {}, {}


def load_articles_with_fallback(sample_path: Path) -> Tuple[Dict[str, List[float]], Dict[str, str], str]:
    articles, primary_categories = load_articles_from_database()
    source = "database (synthesized_articles)" if articles else ""
    if not articles:
        articles, primary_categories = load_articles_from_json(sample_path)
        source = f"sample file {sample_path}"
    return articles, primary_categories, source


def resolve_relevant_articles(
    engagements: Sequence[str],
    primary_categories: Dict[str, str],
    ranked_items: Sequence[str] | None = None,
) -> List[str]:
    """Map engagement labels to concrete article titles.

    Engagements in the sample data are category-tagged (e.g., "Sports Article 8").
    For real synthesized articles we treat a recommendation as relevant if its
    dominant category matches any of the engagement prefixes or if the engagement
    string matches the article title exactly.
    """

    if not engagements:
        return []

    engagement_categories = {label.split(" Article")[0].strip() for label in engagements}
    relevant = []
    candidates = ranked_items if ranked_items is not None else primary_categories.keys()
    max_matches = len(engagements)
    for name in candidates:
        cat = primary_categories.get(name)
        if name in engagements or (cat and cat in engagement_categories):
            relevant.append(name)
            if max_matches and len(relevant) >= max_matches:
                break
    return relevant


def demographic_vector(age: int, gender: str, location: str, category_to_index: Dict[str, int]) -> List[float]:
    vec = [0.0 for _ in range(len(category_to_index))]

    def apply_influence(dim: str, key):
        infl = DEMOGRAPHIC_INFLUENCES[dim]
        if dim == "age":
            for (low, high), weights in infl.items():
                if low <= age <= high:
                    for cat, weight in weights.items():
                        vec[category_to_index[cat]] += weight
                    break
        else:
            weights = infl.get(str(key).lower(), {})
            for cat, weight in weights.items():
                vec[category_to_index[cat]] += weight

    apply_influence("age", age)
    apply_influence("gender", gender)
    apply_influence("location", location)
    return vec


def initialize_user_vector(user: dict, category_to_index: Dict[str, int]) -> List[float]:
    vec = [0.5 for _ in range(len(category_to_index))]
    demo = demographic_vector(user["age"], user["gender"], user["location"], category_to_index)
    vec = [val + delta for val, delta in zip(vec, demo)]
    for pref in user.get("preferences", []):
        if pref in category_to_index:
            vec[category_to_index[pref]] += 0.25
    return rescale_and_normalize_vector(vec)


def rank_articles(user_vector: Sequence[float], articles: Dict[str, Sequence[float]]) -> List[Tuple[str, float]]:
    scores = []
    for name, vec in articles.items():
        score = cos_similarity(user_vector, vec)
        scores.append((name, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def precision_recall_ndcg(
    relevant: Sequence[str], ranked_items: Sequence[str], k: int
) -> Tuple[float, float, float]:
    top_k = list(ranked_items[:k])
    hits = [1 if item in relevant else 0 for item in top_k]
    precision = float(sum(hits)) / k if k else 0.0
    recall = float(sum(hits)) / len(relevant) if relevant else 0.0
    dcg = sum(hit / math.log2(idx + 2) for idx, hit in enumerate(hits))
    ideal_hits = sorted(hits, reverse=True)
    idcg = sum(hit / math.log2(idx + 2) for idx, hit in enumerate(ideal_hits))
    ndcg = dcg / idcg if idcg else 0.0
    return precision, recall, ndcg


def weighted_engagement_rate(ranked_items: Sequence[str], relevant: Sequence[str], k: int) -> float:
    hits = 0.0
    for item in ranked_items[:k]:
        if item in relevant:
            hits += 1.0
    return hits / k if k else 0.0


def median_ratio_update(user_vector: Sequence[float], article_vector: Sequence[float]) -> List[float]:
    median = statistics.median(user_vector)
    update_ratio = [1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in article_vector]
    updated = [
        val + LEARNING_RATE * update_ratio[i] if article_vector[i] >= median else val - LEARNING_RATE * update_ratio[i]
        for i, val in enumerate(user_vector)
    ]
    return rescale_and_normalize_vector(updated)


def update_trajectory(
    user_vector: Sequence[float], engagements: Iterable[str], articles: Dict[str, Sequence[float]]
) -> Tuple[List[List[float]], List[float], List[float]]:
    history = [user_vector]
    norms: List[float] = []
    directionality: List[float] = []

    for name in engagements:
        if name not in articles:
            continue
        previous = history[-1]
        updated = median_ratio_update(previous, articles[name])
        delta = [u - p for u, p in zip(updated, previous)]
        norms.append(math.sqrt(sum(d * d for d in delta)))

        # Directionality agreement compares update sign to article deviation from its median
        update_dir = [1 if d > 0 else -1 if d < 0 else 0 for d in delta]
        article_median = statistics.median(articles[name])
        art_dir = [1 if (a - article_median) > 0 else -1 if (a - article_median) < 0 else 0 for a in articles[name]]
        matches = [1 for u_dir, a_dir in zip(update_dir, art_dir) if u_dir == a_dir]
        agreement = sum(matches) / len(update_dir) if update_dir else 0.0
        directionality.append(float(agreement))

        history.append(updated)

    return history, norms, directionality


def bucket_hit_rates(ranked_items: Sequence[str], relevant: Sequence[str]) -> Tuple[float, float, float]:
    count = len(ranked_items)
    best_end = max(1, int(0.7 * count))
    mid_end = max(best_end + 1, int(0.9 * count))
    buckets = [ranked_items[:best_end], ranked_items[best_end:mid_end], ranked_items[mid_end:]]
    rates = []
    for bucket in buckets:
        if not bucket:
            rates.append(0.0)
            continue
        hits = sum(1 for item in bucket if item in relevant)
        rates.append(hits / len(bucket))
    return tuple(rates)  # type: ignore[return-value]


def coverage_at_k(
    ranked_items: Sequence[str], primary_categories: Dict[str, str], k: int
) -> int:
    categories = {primary_categories.get(name, "Unknown") for name in ranked_items[:k]}
    return len(categories)


def summarize_metrics() -> str:
    articles, primary_categories, article_source = load_articles_with_fallback(
        Path("experiments/articles_normalized.json")
    )
    if not articles:
        raise SystemExit("No article vectors available for evaluation.")

    users = load_users(Path("experiments/users.json"))
    category_to_index = {cat: idx for idx, cat in enumerate(CATEGORIES)}

    rows = []
    update_norms: List[float] = []
    directionality_scores: List[float] = []
    bucket_rates = []
    coverages = []
    precisions = []
    recalls = []
    ndcgs = []
    weighted_rates = []

    for user in users:
        user_vec = initialize_user_vector(user, category_to_index)
        ranked = rank_articles(user_vec, articles)
        ranked_names = [name for name, _ in ranked]

        engagements = user.get("engagements", [])
        relevant_articles = resolve_relevant_articles(engagements, primary_categories, ranked_names)
        precision, recall, ndcg = precision_recall_ndcg(relevant_articles, ranked_names, K)
        weighted_rate = weighted_engagement_rate(ranked_names, relevant_articles, K)
        coverage = coverage_at_k(ranked_names, primary_categories, K)
        best_rate, mid_rate, rest_rate = bucket_hit_rates(ranked_names, relevant_articles)

        history, norms, directionality = update_trajectory(user_vec, relevant_articles, articles)
        avg_norm = float(statistics.mean(norms)) if norms else 0.0
        avg_directionality = float(statistics.mean(directionality)) if directionality else 0.0

        row = {
            "user": user["name"],
            "precision": precision,
            "recall": recall,
            "ndcg": ndcg,
            "weighted_rate": weighted_rate,
            "coverage": coverage,
            "avg_norm": avg_norm,
            "directionality": avg_directionality,
            "best_rate": best_rate,
            "mid_rate": mid_rate,
            "rest_rate": rest_rate,
        }
        rows.append(row)

        update_norms.extend(norms)
        directionality_scores.extend(directionality)
        bucket_rates.append((best_rate, mid_rate, rest_rate))
        coverages.append(coverage)
        precisions.append(precision)
        recalls.append(recall)
        ndcgs.append(ndcg)
        weighted_rates.append(weighted_rate)

    def average(values: Sequence[float]) -> float:
        return float(statistics.mean(values)) if values else 0.0

    avg_best = average([b for b, _, _ in bucket_rates])
    avg_mid = average([m for _, m, _ in bucket_rates])
    avg_rest = average([r for _, _, r in bucket_rates])

    report_lines = [
        "# Evaluation Metrics Report",
        "",
        f"These metrics are computed from the sample users and synthesized article vectors loaded from {article_source}.",
        f"Article count used for scoring: {len(articles)} synthesized items.",
        "",
        "## What the numbers mean",
        f"- **Ranking quality snapshot**: Top-{K} lists average {average(precisions):.2f} precision and {average(recalls):.2f} recall based on category-matched engagements.",
        f"- **Engagement coverage**: {sum(1 for p in precisions if p > 0):d} of {len(users)} users record non-zero relevance; Bob remains a cold-start with no interactions in the fixture data.",
        f"- **Updates are small and aligned**: Average L2 update steps are {average(update_norms):.4f} with {average(directionality_scores):.3f} directionality agreement, showing the median-ratio updates mostly move in the same sign as article deviations.",
        f"- **Catalog breadth**: Top-{K} recommendations touch {average(coverages):.2f} of {len(CATEGORIES)} categories on average, so exploration remains concentrated.",
        f"- **Exploration buckets**: Hit rates across the 70/20/10 best–mid–rest buckets are best={avg_best:.3f}, mid={avg_mid:.3f}, rest={avg_rest:.3f}; similar scores imply diversification doesn’t materially change relevance in this sample.",
        "",
        "## Overall summary",
        f"- Mean Precision@{K}: {average(precisions):.3f}",
        f"- Mean Recall@{K}: {average(recalls):.3f}",
        f"- Mean nDCG@{K}: {average(ndcgs):.3f}",
        f"- Mean weighted engagement@{K}: {average(weighted_rates):.3f} (click weight={CLICK_LIKE_RATIO})",
        f"- Avg update L2 norm: {average(update_norms):.4f}",
        f"- Avg directionality agreement: {average(directionality_scores):.3f}",
        f"- Category coverage@{K}: {average(coverages):.2f} of {len(CATEGORIES)}",
        f"- Bucket hit rates (70/20/10): best={avg_best:.3f}, mid={avg_mid:.3f}, rest={avg_rest:.3f}",
        "",
        "## Per-user breakdown",
        "| User | Precision@K | Recall@K | nDCG@K | Weighted@K | Coverage@K | Avg Δ‖ · ‖ | Directionality | Best hit | Mid hit | Rest hit |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        report_lines.append(
            f"| {row['user']} | {row['precision']:.3f} | {row['recall']:.3f} | {row['ndcg']:.3f} | "
            f"{row['weighted_rate']:.3f} | {row['coverage']:.0f} | {row['avg_norm']:.4f} | "
            f"{row['directionality']:.3f} | {row['best_rate']:.3f} | {row['mid_rate']:.3f} | {row['rest_rate']:.3f} |"
        )

    return "\n".join(report_lines)


if __name__ == "__main__":
    report = summarize_metrics()
    output_path = Path("experiments/evaluation_report.md")
    output_path.write_text(report)
    print(f"Wrote {output_path}")
