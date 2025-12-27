# Evaluation Metrics Report

These metrics are computed from the sample users and synthesized article vectors loaded from database (synthesized_articles).
Article count used for scoring: 94 synthesized items.

## What the numbers mean
- **Ranking quality snapshot**: Top-20 lists average 0.43 precision and 0.43 recall based on category-matched engagements.
- **Engagement coverage**: 2 of 3 users record non-zero relevance.
- **Updates are small and aligned**: Average L2 update steps are 0.0362 with 0.475 directionality agreement, showing the median-ratio updates mostly move in the same sign as article deviations.
- **Catalog breadth**: Top-20 recommendations touch 4.33 of 10 categories on average, so exploration remains concentrated.
- **Exploration buckets**: Hit rates across the 70/20/10 best–mid–rest buckets are best=0.205, mid=0.000, rest=0.000; similar scores imply diversification doesn't materially change relevance in this sample.

## Overall summary
- Mean Precision@20: 0.433
- Mean Recall@20: 0.433
- Mean nDCG@20: 0.522
- Mean weighted engagement@20: 0.433 (click weight=0.25)
- Avg update L2 norm: 0.0362
- Avg directionality agreement: 0.475
- Category coverage@20: 4.33 of 10
- Bucket hit rates (70/20/10): best=0.205, mid=0.000, rest=0.000

## Per-user breakdown
| User | Precision@K | Recall@K | nDCG@K | Weighted@K | Coverage@K | Avg Δ‖ · ‖ | Directionality | Best hit | Mid hit | Rest hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Alice | 0.400 | 0.400 | 0.567 | 0.400 | 5 | 0.0417 | 0.395 | 0.308 | 0.000 | 0.000 |
| Bob | 0.000 | 0.000 | 0.000 | 0.000 | 4 | 0.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Carol | 0.900 | 0.900 | 0.998 | 0.900 | 4 | 0.0308 | 0.555 | 0.308 | 0.000 | 0.000 |

## Learning Trajectory Visualizations

The following charts show how each user's interest vector evolves through their engagement history:

### Alice
![Alice Learning Trajectory](learning_trajectory_alice.png)

### Carol
![Carol Learning Trajectory](learning_trajectory_carol.png)
