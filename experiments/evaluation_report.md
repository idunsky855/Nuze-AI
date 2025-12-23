# Evaluation Metrics Report

These metrics are computed from the sample users and synthesized article vectors loaded from database (synthesized_articles).
Article count used for scoring: 762 synthesized items.

## What the numbers mean
- **Ranking quality snapshot**: Top-20 lists average 0.92 precision and 0.92 recall based on category-matched engagements.
- **Engagement coverage**: 3 of 3 users record non-zero relevance.
- **Updates are small and aligned**: Average L2 update steps are 0.0396 with 0.752 directionality agreement, showing the median-ratio updates mostly move in the same sign as article deviations.
- **Catalog breadth**: Top-20 recommendations touch 5.00 of 10 categories on average, so exploration remains concentrated.
- **Exploration buckets**: Hit rates across the 70/20/10 best–mid–rest buckets are best=0.038, mid=0.000, rest=0.000; similar scores imply diversification doesn't materially change relevance in this sample.

## Overall summary
- Mean Precision@20: 0.917
- Mean Recall@20: 0.917
- Mean nDCG@20: 0.933
- Mean weighted engagement@20: 0.917 (click weight=0.25)
- Avg update L2 norm: 0.0396
- Avg directionality agreement: 0.752
- Category coverage@20: 5.00 of 10
- Bucket hit rates (70/20/10): best=0.038, mid=0.000, rest=0.000

## Per-user breakdown
| User | Precision@K | Recall@K | nDCG@K | Weighted@K | Coverage@K | Avg Δ‖ · ‖ | Directionality | Best hit | Mid hit | Rest hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Alice | 0.900 | 0.900 | 0.993 | 0.900 | 5 | 0.0377 | 0.755 | 0.038 | 0.000 | 0.000 |
| Bob | 0.900 | 0.900 | 0.822 | 0.900 | 4 | 0.0431 | 0.685 | 0.038 | 0.000 | 0.000 |
| Carol | 0.950 | 0.950 | 0.984 | 0.950 | 6 | 0.0380 | 0.815 | 0.038 | 0.000 | 0.000 |

## Learning Trajectory Visualizations

The following charts show how each user's interest vector evolves through their engagement history:

### Alice
![Alice Learning Trajectory](learning_trajectory_alice.png)

### Bob
![Bob Learning Trajectory](learning_trajectory_bob.png)

### Carol
![Carol Learning Trajectory](learning_trajectory_carol.png)
