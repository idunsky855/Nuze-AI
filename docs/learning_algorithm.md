# Learning Algorithm: Mathematical Breakdown

This document provides a mathematical formalization of the user preference learning algorithm used in Nuze.

## 1. Vector Representation

### User Vector
$$\mathbf{u} = [u_1, u_2, ..., u_{10}, m_1, m_2, ..., m_5] \in \mathbb{R}^{15}$$

Where:
- $u_i$ = interest score for category $i$ (10 categories)
- $m_j$ = preference for metadata dimension $j$ (5 dimensions: Length, Complexity, Neutral, Informative, Emotional)

### Article Vector
$$\mathbf{a} = [a_1, a_2, ..., a_{10}, \mu_1, \mu_2, ..., \mu_5] \in \mathbb{R}^{15}$$

---

## 2. Initialization

### Base Vector
$$u_i^{(0)} = 0.5 \quad \forall i \in \{1, ..., 15\}$$

### Demographic Adjustment
$$\mathbf{u}^{(1)} = \mathbf{u}^{(0)} + \mathbf{d}(\text{age}, \text{gender}, \text{location})$$

Where $\mathbf{d}$ encodes demographic influences (see `DEMOGRAPHIC_INFLUENCES` lookup table).

### Preference Boost
For each selected preference category $p$:
$$u_p^{(2)} = u_p^{(1)} + 0.25$$

### Normalization
After adjustments, the category portion is rescaled:
$$u_i^{\text{norm}} = u_i \cdot \frac{5.0}{\sum_{j=1}^{10} |u_j|}$$

---

## 3. Median-Ratio Update Algorithm

The core learning mechanism uses a **median-ratio update rule**.

### Step 1: Compute Median
$$\tilde{u} = \text{median}(\mathbf{u})$$

### Step 2: Compute Update Ratio
For each dimension $i$:

$$r_i = \begin{cases}
1 - \dfrac{a_i}{\tilde{u}} & \text{if } a_i \leq \tilde{u} \\[2ex]
1 - \dfrac{\tilde{u}}{a_i} & \text{if } a_i > \tilde{u}
\end{cases}$$

**Intuition**: $r_i$ measures how far the article value deviates from the user's median, normalized to $[0, 1)$.

### Step 3: Apply Update

Given learning rate $\eta = 0.016$:

#### Like (Strengthen)
$$u_i^{\text{new}} = \begin{cases}
u_i + \eta \cdot r_i & \text{if } a_i \geq \tilde{u} \\
u_i - \eta \cdot r_i & \text{if } a_i < \tilde{u}
\end{cases}$$

#### Dislike (Weaken)
$$u_i^{\text{new}} = \begin{cases}
u_i + \eta \cdot r_i & \text{if } a_i \leq \tilde{u} \\
u_i - \eta \cdot r_i & \text{if } a_i > \tilde{u}
\end{cases}$$

#### Click (Implicit Feedback)
Uses same logic as **Like**, but with reduced learning rate:
$$\eta_{\text{click}} = 0.25 \cdot \eta = 0.004$$

---

## 4. Post-Update Processing

### Category Normalization
$$u_i^{\text{final}} = u_i^{\text{new}} \cdot \frac{5.0}{\sum_{j=1}^{10} |u_j^{\text{new}}|}$$

### Metadata Clipping
$$m_j^{\text{final}} = \text{clip}(m_j^{\text{new}}, 0, 1)$$

---

## 5. Algorithm Summary

```
Input: user_vector u, article_vector a, feedback ∈ {like, dislike, click}
Output: updated user_vector u'

1. median ← median(u)
2. for i = 1 to 15:
     if a[i] ≤ median:
       r[i] ← 1 - a[i]/median
     else:
       r[i] ← 1 - median/a[i]

3. η ← 0.016 if feedback ∈ {like, dislike} else 0.004

4. for i = 1 to 15:
     if feedback = like or feedback = click:
       u'[i] ← u[i] + η·r[i]  if a[i] ≥ median else u[i] - η·r[i]
     else:  # dislike
       u'[i] ← u[i] + η·r[i]  if a[i] ≤ median else u[i] - η·r[i]

5. Normalize categories: u'[1:10] ← rescale(u'[1:10], target=5.0)
6. Clip metadata: u'[11:15] ← clip(u'[11:15], 0, 1)

return u'
```

---

## 6. Key Properties

| Property | Value |
|----------|-------|
| Learning Rate (η) | 0.016 |
| Click Learning Rate | 0.004 (25% of η) |
| Category Dimensions | 10 |
| Metadata Dimensions | 5 |
| Total Vector Size | 15 |
| Category Target Sum | 5.0 |
| Initial Value | 0.5 |
| Preference Boost | +0.25 |

---

## 7. Convergence Behavior

The algorithm exhibits the following properties:

1. **Bounded Updates**: Since $r_i \in [0, 1)$ and $\eta$ is small, updates are bounded.
2. **Shape Preservation**: Normalization ensures the category vector maintains constant L1 norm.
3. **Asymmetric Learning**: Opposing feedback (like vs. dislike) moves the vector in opposite directions along the same dimensions.
4. **Implicit vs. Explicit**: Clicks provide weaker signals than explicit likes/dislikes.

---

## 8. Similarity Metric

For article ranking, median-deviation shape similarity is used:

$$\text{sim}(\mathbf{u}, \mathbf{a}) = \sum_{i=1}^{n} \begin{cases}
\dfrac{a_i}{\tilde{u}} - 1 & \text{if } a_i \leq \tilde{u} \\[2ex]
\dfrac{\tilde{u}}{a_i} - 1 & \text{if } a_i > \tilde{u}
\end{cases}$$

Higher similarity indicates better alignment between user preferences and article characteristics.

---

## 9. Alternative Algorithms Evaluated

During experimentation, several alternative approaches were tested:

### 9.1 Similarity Metrics

Three similarity metrics were compared (configurable via `SIMILARITY` parameter):

#### Cosine Similarity
$$\text{sim}_{\cos}(\mathbf{u}, \mathbf{a}) = \frac{\mathbf{u} \cdot \mathbf{a}}{\|\mathbf{u}\| \cdot \|\mathbf{a}\|}$$

**Properties**: Measures angle between vectors, range $[-1, 1]$.

#### KL Divergence
$$D_{KL}(P \| Q) = \sum_i P_i \log\frac{P_i}{Q_i}$$

Where $P$ and $Q$ are normalized probability distributions. Like probability computed as:
$$p_{\text{like}} = e^{-3 \cdot D_{KL}}$$

**Properties**: Asymmetric, measures information loss, always $\geq 0$.

#### Median-Deviation Shape Similarity (Selected)
$$\text{sim}_{\text{med}}(\mathbf{u}, \mathbf{a}) = \frac{(\mathbf{u} - \tilde{u})^T \cdot (\mathbf{a} - \tilde{a})}{\|\mathbf{u} - \tilde{u}\| \cdot \|\mathbf{a} - \tilde{a}\|}$$

**Properties**: Centers both vectors around their medians before computing cosine, robust to outliers.

---

### 9.2 Update Algorithms

#### Simple Median-Based Update (Alternative 1)

A simpler update that doesn't consider article values:

**Strengthen:**
$$u_i^{\text{new}} = \begin{cases}
u_i + \eta & \text{if } u_i \geq \tilde{u} \\
u_i - \eta & \text{if } u_i < \tilde{u}
\end{cases}$$

**Weaken:**
$$u_i^{\text{new}} = \begin{cases}
u_i - \eta & \text{if } u_i \geq \tilde{u} \\
u_i + \eta & \text{if } u_i < \tilde{u}
\end{cases}$$

**Limitation**: Ignores article content - only amplifies/dampens existing preferences.

---

#### Median-Ratio Update (Selected)

The production algorithm that uses the article vector to guide updates:

$$r_i = \begin{cases}
1 - \dfrac{a_i}{\tilde{u}} & \text{if } a_i \leq \tilde{u} \\[2ex]
1 - \dfrac{\tilde{u}}{a_i} & \text{if } a_i > \tilde{u}
\end{cases}$$

**Strengthen:**
$$u_i^{\text{new}} = u_i + \text{sign}(a_i - \tilde{u}) \cdot \eta \cdot r_i$$

**Advantage**: Updates are proportional to how extreme the article's values are relative to the user's median.

---

### 9.3 Algorithm Comparison Summary

| Algorithm | Article-Aware | Bounded Updates | Chosen |
|-----------|--------------|-----------------|--------|
| Simple Median | ❌ | ✅ | ❌ |
| Median-Ratio | ✅ | ✅ | ✅ |
| Cosine Sim | ✅ | ✅ | ❌ |
| KL Divergence | ✅ | ✅ | ❌ |

**Why Median-Ratio was selected:**
1. **Article-aware**: Updates reflect the specific article content, not just user history
2. **Bounded updates**: The ratio $r_i \in [0, 1)$ ensures stability
3. **Interpretable**: Updates are proportional to deviation from user's central tendency
4. **Robust**: Median is less sensitive to outliers than mean
