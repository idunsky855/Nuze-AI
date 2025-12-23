# Evaluation Metrics Report

These metrics are computed from the sample users and synthesized article vectors loaded from sample file experiments/articles_normalized.json.
Article count used for scoring: 200 synthesized items.

## What the numbers mean
- **Ranking quality snapshot**: Top-5 lists average 0.67 precision and 0.17 recall based on category-matched engagements.
- **Engagement coverage**: 2 of 3 users record non-zero relevance; Bob remains a cold-start with no interactions in the fixture data.
- **Updates are small and aligned**: Average L2 update steps are 0.0198 with 0.912 directionality agreement, showing the median-ratio updates mostly move in the same sign as article deviations.
- **Catalog breadth**: Top-5 recommendations touch 2.67 of 10 categories on average, so exploration remains concentrated.
- **Exploration buckets**: Hit rates across the 70/20/10 best–mid–rest buckets are best=0.095, mid=0.000, rest=0.000; similar scores imply diversification doesn’t materially change relevance in this sample.

## Overall summary
- Mean Precision@5: 0.667
- Mean Recall@5: 0.167
- Mean nDCG@5: 0.667
- Mean weighted engagement@5: 0.667 (click weight=0.25)
- Avg update L2 norm: 0.0198
- Avg directionality agreement: 0.912
- Category coverage@5: 2.67 of 10
- Bucket hit rates (70/20/10): best=0.095, mid=0.000, rest=0.000

## Per-user breakdown
| User | Precision@K | Recall@K | nDCG@K | Weighted@K | Coverage@K | Avg Δ‖ · ‖ | Directionality | Best hit | Mid hit | Rest hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Alice | 1.000 | 0.250 | 1.000 | 1.000 | 2 | 0.0195 | 0.905 | 0.143 | 0.000 | 0.000 |
| Bob | 0.000 | 0.000 | 0.000 | 0.000 | 4 | 0.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Carol | 1.000 | 0.250 | 1.000 | 1.000 | 2 | 0.0201 | 0.920 | 0.143 | 0.000 | 0.000 |