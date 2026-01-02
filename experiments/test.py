import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils import * 
from rich import print
from article import Article
from scipy.stats import pearsonr

random.seed(42)                         # Seed for randomness simulation
INIT_VALUE = 0.5                        # Vector first value for uniform distribution 
SIMILARITY = "median"                   # options - "median", "cosine", "kl divergence"
LEARNING_RATE = 0.016                   # Learning rate
BUCKET_SIZE = 10                        # For division into 3 article buckets [high, mid, low]
RANDOMNESS_PROBS = [0.75, 0.20, 0.05]   # The probabilities to choose an article from each bucket.
ENGAGMENT_STEPS = 50                    # Number of engagement steps

#####################################################################################################################################
##                                                       --- Category Setup ---                                                    ##
#####################################################################################################################################
categories = [
    "Politics & Law",
    "Economy & Business",
    "Science & Technology",
    "Health & Wellness",
    "Education & Society",
    "Culture & Entertainment",
    "Religion & Belief",
    "Sports",
    "World & International Affairs",
    "Opinion & General News"
]

CATEGORY_DIM = len(categories)
category_to_index = {cat: idx for idx, cat in enumerate(categories)}

#####################################################################################################################################
##                                                       --- Metadata Setup ---                                                    ##
#####################################################################################################################################
metadata_labels = ["Length", "Complexity", "Tone","Content Type", "Named Entities"]
metadata = {
    "Length": 0.8,
    "Complexity": 0.6,
    "Tone": {"Neutral": 0.7, "Informative": 0.8, "Emotional": 0.1},
    "Content_type": "Analysis",
    "Named Entities": ["Temu", "Biden", "CBP", "de minimis rule"]
}

metadata_info = [
    "static",
    "static",
    "dynamic",
    "dynamic",
    "dynamic"
]
metadata_to_index = {cat: idx + CATEGORY_DIM for idx, cat in enumerate(metadata_labels)}
METADATA_DIM = len(metadata_info)
#####################################################################################################################################
##                                                     Demographic influence weights                                               ##
#####################################################################################################################################
DEMOGRAPHIC_INFLUENCES = {
    'age': {
        # Ages 0–17: 
        #   +Culture, +Science, +Sports  |  –Politics, –World, –Health
        (0, 17): {
            'Culture & Entertainment':            0.15,
            'Science & Technology':               0.10,
            'Sports':                             0.05,
            'Politics & Law':                    -0.15,
            'World & International Affairs':     -0.10,
            'Health & Wellness':                 -0.05
        },
        # Ages 18–24:
        #   +Culture, +Science, +Sports  |  –Politics, –Economy, –Opinion
        (18, 24): {
            'Culture & Entertainment':            0.10,
            'Science & Technology':               0.10,
            'Sports':                             0.05,
            'Politics & Law':                    -0.10,
            'Economy & Business':               -0.10,
            'Opinion & General News':            -0.05
        },
        # Ages 25–34:
        #   +Science, +Economy, +Culture  |  –Education, –Opinion, –Sports
        (25, 34): {
            'Science & Technology':               0.10,
            'Economy & Business':                 0.07,
            'Culture & Entertainment':            0.05,
            'Education & Society':               -0.10,
            'Opinion & General News':            -0.07,
            'Sports':                            -0.05
        },
        # Ages 35–49:
        #   +Health, +Education, +Opinion  |  –Science, –Culture, –Economy
        (35, 49): {
            'Health & Wellness':                 0.10,
            'Education & Society':                0.07,
            'Opinion & General News':             0.05,
            'Science & Technology':              -0.05,
            'Culture & Entertainment':           -0.10,
            'Economy & Business':               -0.07
        },
        # Ages 50–64:
        #   +Health, +Opinion  |  –Economy, –Education, –Science
        (50, 64): {
            'Health & Wellness':                 0.12,
            'Opinion & General News':             0.10,
            'Economy & Business':               -0.10,
            'Education & Society':               -0.05,
            'Science & Technology':              -0.07
        },
        # Ages 65–100:
        #   +Health, +Opinion  |  –Economy, –Education, –Science
        (65, 100): {
            'Health & Wellness':                 0.15,
            'Opinion & General News':             0.10,
            'Economy & Business':               -0.10,
            'Education & Society':               -0.10,
            'Science & Technology':              -0.05
        },
    },

    'gender': {
        # Female: +Health, +Opinion  |  –Sports, –Economy
        'female': {
            'Health & Wellness':                  0.08,
            'Opinion & General News':             0.05,
            'Sports':                            -0.08,
            'Economy & Business':               -0.05
        },
        # Male: +Sports, +Science  |  –Health, –Opinion
        'male': {
            'Sports':                             0.08,
            'Science & Technology':               0.05,
            'Health & Wellness':                -0.08,
            'Opinion & General News':           -0.05
        },
        # Unknown gender: no net influence
        'unknown': {}
    },

    'location': {
        # Urban: +Politics, +World, +Economy  |  –Culture, –Health, –Education, –Sports  →  sum = 0
        'urban': {
            'Politics & Law':                     0.10,
            'World & International Affairs':      0.10,
            'Economy & Business':                 0.05,
            'Culture & Entertainment':           -0.10,
            'Health & Wellness':                 -0.05,
            'Education & Society':               -0.05,
            'Sports':                            -0.05
            # (Science, Religion, Opinion remain 0)
        },
        # Suburban: +Education, +Culture  |  –Politics, –Economy, –Sports  →  sum = 0
        'suburban': {
            'Education & Society':                0.10,
            'Culture & Entertainment':             0.05,
            'Politics & Law':                    -0.05,
            'Economy & Business':               -0.05,
            'Sports':                            -0.05
            # (Science, Health, Religion, World, Opinion remain 0)
        },
        # Rural: +Economy, +Education  |  –Science, –Culture, –Health  →  sum = 0
        'rural': {
            'Economy & Business':                 0.10,
            'Education & Society':                0.05,
            'Science & Technology':              -0.05,
            'Culture & Entertainment':           -0.05,
            'Health & Wellness':                 -0.05
            # (Politics, Religion, Sports, World, Opinion remain 0)
        },
        # Unknown location: no net influence
        'unknown': {}
    }
}

def encode_demographics(age, gender, location, normalize=True):
    """
    Returns a CATEGORY_DIM vector of small 'nudges' per demographic.
    """
    vec = np.zeros(CATEGORY_DIM)

    def apply_influence(dim, key):
        infl = DEMOGRAPHIC_INFLUENCES[dim]
        if dim == 'age':
            for (low, high), weights in infl.items():
                if low <= age <= high:
                    for cat, w in weights.items():
                        vec[category_to_index[cat]] += w
                    break
        else:
            # lower-case lookup for gender/location
            weights = infl.get(key.lower(), {})
            for cat, w in weights.items():
                vec[category_to_index[cat]] += w

    apply_influence('age', age)
    apply_influence('gender', gender)
    apply_influence('location', location)

    return vec


def update_demographics(vec : np.array, categories_dim: int, age: int, gender: str, location: str) -> np.array:
    """
    Returns a CATEGORY_DIM vector of small 'nudges' per demographic.
    """
    user_categories_vec = vec[:categories_dim]
    user_categories_metadata = vec[categories_dim:]

    user_categories_vec += encode_demographics(age, gender, location)

    return np.concatenate([rescale_and_normalize_vector(user_categories_vec),user_categories_metadata], axis=0)

#####################################################################################################################################
##                                                         --- Vector Update ---                                                   ##
##################################################################################################################################### 
def calc_like_chance(vec: np.array=None, article: Article=None,sharpness: float=-3.0) -> float:
    """Calcuates the chance for a like based on similarity score and method.

    Args:
        vec (np.array, optional): User interests vector. Defaults to None.
        art_vec (Article, optional): Article. Defaults to None.
        sharpness (float, optional): sharpness value for kl divergence. Defaults to -3.0.

    Returns:
        float: like chance
    """
    if SIMILARITY == "cosine":
        # Pearson correlation with cosine similarity
        corr_like_prob = pearsonr(vec, article.get_full_vector()).statistic
        like_prob = corr_like_prob
    elif SIMILARITY == "kl divergence":
        # KL-Divergence as similarity
        kl_divergenece_like_prob = np.exp(sharpness * article.get_sim())    
        like_prob = kl_divergenece_like_prob
    elif SIMILARITY == "median":
        # Median deviation shape similarity
        sigmoid_like_prob = sigmoid(article.get_sim())        
        like_prob = sigmoid_like_prob
    else:
        raise ValueError("SIMILARITY is not defined properly")
    
    return like_prob


def update_preferences(user_vec: np.array,categories_dim: int ,preferences: dict) -> np.array:
    # Apply preference boost
    for pref in preferences["categories"]:
        if pref in category_to_index:
            user_vec[category_to_index[pref]] += 0.25   # override to strong interest
            
    for pref, val in preferences["metadata"].items():
        if pref in metadata.keys():
            user_vec[metadata_to_index[pref]] = val
            
    return np.concatenate([rescale_and_normalize_vector(user_vec[:categories_dim]),user_vec[categories_dim:]], axis=0)

def is_liked(prob: float) -> bool:
    """
    Decide if liked based on probability.
    """
    return np.random.rand() < prob

def strengthen_user_vector(user_vector: np.array, learning_rate=0.1):
    """
    Strengthens a user vector by adjusting its values relative to the median and normalizing the result.
    Each value in the input vector is increased by the learning rate if it is greater than or equal to the median,
    or decreased by the learning rate if it is less than the median. The resulting vector is then rescaled and normalized.
    Args:
        user_vector (np.array): The input user vector to be strengthened.
        learning_rate (float, optional): The amount by which to adjust each value. Defaults to 0.05.
    Returns:
        np.array: The rescaled and normalized strengthened user vector.
    """
    
    median = np.median(user_vector)
    return rescale_and_normalize_vector(np.array([val + learning_rate if val >= median else val - learning_rate for val in user_vector]))

def weaken_user_vector(user_vector: np.array, learning_rate=0.05):
    """
    Adjusts the values of a user vector by weakening values above or equal to the median and strengthening those below the median.
    For each element in the input vector:
        - If the value is greater than or equal to the median, it is decreased by the learning rate.
        - If the value is less than the median, it is increased by the learning rate.
    The resulting vector is then rescaled and normalized.
    Args:
        user_vector (np.array): The input user vector to be adjusted.
        learning_rate (float, optional): The amount by which to adjust each value. Defaults to 0.05.
    Returns:
        np.array: The rescaled and normalized adjusted user vector.
    """
    
    median = np.median(user_vector)
    return rescale_and_normalize_vector(np.array([val - learning_rate if val >= median else val + learning_rate for val in user_vector]))

def strengthen_user_vector_by_median_ratio(user_vector: np.array, article: Article, learning_rate=0.05):
    """
    Strengthens the user vector by adjusting its values based on the median ratio with respect to an article vector.
    For each dimension, the function computes an update ratio based on the median of the user vector and the corresponding value in the article vector. 
    If the article's value is greater than or equal to the median, the user vector is increased by a fraction of the update ratio; 
    otherwise, it is decreased. The updated vector is then rescaled and normalized.
    Args:
        user_vector (np.array): The current user vector.
        article (Article): The article object containing the vector to compare against.
        step (optional): Unused parameter, kept for compatibility.
        learning_rate (float, optional): The rate at which to update the user vector. Default is 0.05.
    Returns:
        np.array: The updated, rescaled, and normalized user vector.
    """
    
    categories_dim = article.get_category_dim()
    
    user_categories_vec = user_vector[:categories_dim]
    user_metadata = user_vector[categories_dim:]
    median = np.median(user_categories_vec)
    art_categories_vec = np.array(article.get_category_vector())

    update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in art_categories_vec])
    updated_vec = np.array([val + learning_rate * update_ratio[i] if art_categories_vec[i] >= median else val - learning_rate * update_ratio[i] for i, val in enumerate(user_categories_vec)])
    return np.concatenate([rescale_and_normalize_vector(updated_vec),user_metadata], axis=0)
    
def weaken_user_vector_by_vector_median_ratio(user_vector: np.array, article: Article, learning_rate=0.05):
    """
    Adjusts the user vector by weakening its values based on the median ratio with the article vector.
    For each dimension, the function computes an update ratio relative to the median of the user vector and the 
    corresponding value in the article vector. The user vector is then updated by either increasing or decreasing each value 
    by a scaled amount, depending on whether the article vector's value is above or below the median. The updated vector is then rescaled and normalized.
    Args:
        user_vector (np.array): The user's vector representation.
        article (Article): The article object providing a vector for comparison.
        step (optional): Unused parameter for compatibility.
        learning_rate (float, optional): The scaling factor for the update. Defaults to 0.05.
    Returns:
        np.array: The rescaled and normalized updated user vector.
    """
    categories_dim = article.get_category_dim()

    user_categories_vec = user_vector[:categories_dim]
    user_metadata = user_vector[categories_dim:] 
    median = np.median(user_categories_vec)
    art_categories_vec = np.array(article.get_category_vector())
    
    update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in art_categories_vec])
    updated_vec = np.array([val + learning_rate * update_ratio[i] if art_categories_vec[i] <= median else val - learning_rate * update_ratio[i] for i, val in enumerate(user_categories_vec)])
    return np.concatenate([rescale_and_normalize_vector(updated_vec),user_metadata], axis=0)

def strengthen_user_metadata_by_median_ratio(user_vector: np.array, metadata_config: np.array, article: Article, learning_rate=0.05):

    categories_dim = article.get_category_dim()
    
    user_metadata = user_vector[categories_dim:]
    user_categories_vector = user_vector[:categories_dim]
    median = np.median(user_metadata)
    article_metadata = np.array(article.get_metadata())
  
    update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in article_metadata])
    
    updated_user_metadata_vec = np.array([
    val + learning_rate * update_ratio[i] if article_metadata[i] >= median and metadata_config[metadata_labels[i]] == False         # If metadata category is static
    else val - learning_rate * update_ratio[i] if article_metadata[i] < median and metadata_config[metadata_labels[i]] == False     # If metadata category is static
    else val
    for i, val in enumerate(user_metadata)
    ])
    
    return np.concatenate([user_categories_vector ,np.clip(updated_user_metadata_vec, 0, 1)], axis=0)  

def weaken_user_metadata_by_median_ratio(user_vector: np.array, metadata_config: np.array ,article: Article, learning_rate=0.05):

    categories_dim = article.get_category_dim()

    user_metadata = user_vector[categories_dim:]
    user_categories_vector = user_vector[:categories_dim]
    median = np.median(user_metadata)
    article_metadata = np.array(article.get_metadata())
    
       
    update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in article_metadata])

    updated_user_metadata_vec = np.array([
        val + learning_rate * update_ratio[i]
        if article_metadata[i] <= median and metadata_config[metadata_labels[i]] == False  # If metadata category is static
        else val - learning_rate * update_ratio[i]
        if article_metadata[i] > median and metadata_config[metadata_labels[i]] == False   # If metadata category is static
        else val
        for i, val in enumerate(user_metadata)
    ])
    
    return np.concatenate([user_categories_vector ,np.clip(updated_user_metadata_vec, 0, 1)], axis=0)  


def order_articles_for_user(user_vec : np.array)-> list[Article]:
    """
    Order all articles based on similarity with the users vector.
    
    Args:
        user_vec (np.ndarray): Vector to score article similarities.
    
    Returns:
        list[Article]: One randomly chosen article.
    """
    
    sim_func = None
     
    if SIMILARITY == "cosine":
        sim_func = cos_similarity
    elif SIMILARITY == "kl divergence":
        sim_func = kl_divergence
    elif SIMILARITY == "median":
        sim_func = median_deviation_shape_similarity
    else:
        raise ValueError("SIMILARITY is not defined properly")
    

    # Calculate similarity for each article
    for article in articles:
        article.set_sim(sim_func(user_vec, article.get_full_vector()))  # Median deviation shape
        
    # Sort by similarity
    articles.sort(key=lambda article: article.get_sim(), reverse=True)
    return articles

def get_article_for_user(user_vec: np.ndarray) -> Article:
    """
    Select one Article by sampling:
      - 75% chance from top 10 most similar,
      - 20% from ranks 11–20,
      -  5% from the rest.
    
    Args:
        user_vec (np.ndarray): Vector to score article similarities.
    
    Returns:
        Article: One randomly chosen article.
    
    Raises:
        ValueError: If no articles are available.
    """
    
    # Sort & take slices
    ordered = order_articles_for_user(user_vec)
    best  = ordered[:BUCKET_SIZE]
    mid   = ordered[BUCKET_SIZE:2*BUCKET_SIZE]      # articles ranked 11–20
    rest  = ordered[2*BUCKET_SIZE:]        # rank 21 onward

    # Sample a bucket by your probabilities
    r = np.random.rand()
    if r < RANDOMNESS_PROBS[0] and best:
        pool = best
    elif r < RANDOMNESS_PROBS[0] + RANDOMNESS_PROBS[1] and mid:
        pool = mid
    else:
        pool = rest if rest else (mid or best)

    # Pick one article uniformly
    article = random.choice(pool)

    articles.remove(article)  # Remove from the pool to avoid duplicates in the next steps
    return article

#####################################################################################################################################
##                                                         ---- EXAMPLE ----                                                       ##
#####################################################################################################################################

if __name__ == "__main__":
    interaction = pd.DataFrame(columns=["user" ,"step", "similarity", "like_prob", "liked", "article vector", "user vector", "sum", "metadata"])
    articles = load_article_vectors(json_path="articles.json")
    users = load_users()
    user = users[1] # 1 - Alice, 2 - Bob, 3 - Carol
    bob_vecs = []
    articles_vecs = []
    articles_like_probs = []
    user_vector_history = []  # Store history for plotting
    
    # Cold vector initialization
    init_vec = np.ones(CATEGORY_DIM + METADATA_DIM) * INIT_VALUE
    bob_vecs.append(init_vec)
    user_vector_history.append(init_vec.copy())
    interaction.loc[len(interaction)] = [user['name'], "Init", None, None, None, None, init_vec, np.sum(init_vec[:CATEGORY_DIM]), init_vec[CATEGORY_DIM:]]

    # Demographics based vector update
    demo_vec = update_demographics(init_vec.copy(), CATEGORY_DIM, user["age"], user["gender"], user["location"])
    bob_vecs.append(demo_vec)
    user_vector_history.append(demo_vec.copy())
    dem_del_vec = demo_vec -  init_vec
    interaction.loc[len(interaction)] = [user['name'], "Demographics", None, None, None, None, demo_vec, np.sum(demo_vec[:CATEGORY_DIM]), demo_vec[CATEGORY_DIM:]]
    
    # Preferences based vector update
    pref_vec = update_preferences(demo_vec.copy(), CATEGORY_DIM, user["preferences"])
    bob_vecs.append(pref_vec)
    user_vector_history.append(pref_vec.copy())
    dem_del_vec = pref_vec - demo_vec
    interaction.loc[len(interaction)] = [user['name'], "Preferences", None, None, None, None, pref_vec, np.sum(pref_vec[:CATEGORY_DIM]), pref_vec[CATEGORY_DIM:]]


    # Engagement steps
    for i in range(ENGAGMENT_STEPS):
        curr_vec = bob_vecs[-1]
        chosen_article = get_article_for_user(curr_vec)
        article_vec = np.array(chosen_article.get_full_vector())
        articles_vecs.append(article_vec)
        like_prob = calc_like_chance(curr_vec, chosen_article)
        articles_like_probs.append(like_prob) 
        liked = is_liked(articles_like_probs[-1]) 
        # liked = like_prob >= 0.5 
        if liked:
            strengthen_user_categories_vector = strengthen_user_vector_by_median_ratio(curr_vec, chosen_article, learning_rate=LEARNING_RATE)
            new_vec = strengthen_user_metadata_by_median_ratio(strengthen_user_categories_vector, user['preferences']["static_metadata_conf"], chosen_article, learning_rate=LEARNING_RATE)
            # new_vec = strengthen_user_vector(curr_vec)
        else:
            weaken_user_categories_vector = weaken_user_vector_by_vector_median_ratio(curr_vec, chosen_article, learning_rate=LEARNING_RATE)
            new_vec = weaken_user_metadata_by_median_ratio(weaken_user_categories_vector, user['preferences']["static_metadata_conf"], chosen_article, learning_rate=LEARNING_RATE)
            # new_vec = weaken_user_vector(curr_vec)

        bob_vecs.append(new_vec)
        user_vector_history.append(new_vec.copy())
    
        interaction.loc[len(interaction)] = [user['name'], f"Step: {i}", chosen_article.get_sim(), like_prob, liked, article_vec, curr_vec, np.sum(curr_vec[:CATEGORY_DIM]), curr_vec[CATEGORY_DIM:]]
    

    print(interaction[interaction["liked"] == True].count())
    
    # Print the DataFrame with numerical values rounded to 3 decimals
    # Round each vector column to 3 decimals for display
    interaction_display = interaction.copy()
    for col in ["article vector", "user vector", "metadata"]:
        interaction_display[col] = interaction_display[col].apply(lambda v: np.round(v, 2) if isinstance(v, np.ndarray) else v)
    
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_seq_items', None)
    pd.set_option('display.width', 200)
    

    print(interaction_display.round(2))
    
    # Interactive plot with article vector points overlay and like status as stars
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider

    user_vector_history = np.array(user_vector_history)
    article_vectors = np.array([v for v in interaction["article vector"].tolist() if isinstance(v, np.ndarray)])
    liked_status = interaction["liked"].tolist()[3:]  # skip first 3 non-engagement steps
    steps = len(user_vector_history)

    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    plt.subplots_adjust(bottom=0.2)

    category_lines = []
    article_point_plots = []

    # Initial plot for categories
    for dim in range(CATEGORY_DIM):
        (line,) = axs[0].plot(user_vector_history[:, dim], label=categories[dim])
        category_lines.append(line)
        # Scatter for article vector points (one per step, but only one visible at a time)
        (art_point,) = axs[0].plot([], [], marker='o', color=line.get_color(), markersize=10, alpha=0.7)
        article_point_plots.append(art_point)

    axs[0].set_title(f"User Category Vector Evolution for {user['name']}")
    axs[0].set_ylabel("Interest Value")
    axs[0].set_ylim(0, 1)
    axs[0].legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    axs[0].grid(True)

    # Metadata plot
    metadata_labels = ["Length", "Complexity", "Neutral", "Informative", "Emotional"]
    metadata_lines = []
    article_metadata_point_plots = []
    for dim in range(METADATA_DIM):
        (line,) = axs[1].plot(user_vector_history[:, CATEGORY_DIM + dim], label=metadata_labels[dim])
        metadata_lines.append(line)
        (art_point,) = axs[1].plot([], [], marker='o', color=line.get_color(), markersize=10, alpha=0.7)
        article_metadata_point_plots.append(art_point)

    axs[1].set_title(f"User Metadata Evolution for {user['name']}")
    axs[1].set_xlabel("Step")
    axs[1].set_ylabel("Metadata Value")
    axs[1].set_ylim(0, 1)
    axs[1].legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    axs[1].grid(True)

    # Slider for step selection
    ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
    step_slider = Slider(ax_slider, 'Step', 0, steps-1, valinit=0, valstep=1)


    def update(val):
        idx = int(step_slider.val)
        art_idx = idx - 3  # Skip non-engagement steps

        # Update user vector lines (category and metadata)
        for dim in range(CATEGORY_DIM):
            category_lines[dim].set_data(range(idx + 1), user_vector_history[:idx + 1, dim])

        for dim in range(METADATA_DIM):
            metadata_lines[dim].set_data(range(idx + 1), user_vector_history[:idx + 1, CATEGORY_DIM + dim])

        axs[0].set_xlim(0, steps)
        axs[1].set_xlim(0, steps)

        # Update article vector markers offset to the right of the step
        if 0 <= art_idx < len(article_vectors):
            art_vec = article_vectors[art_idx]
            liked = liked_status[art_idx]
            marker_style = '*' if liked else 'o'
            marker_offset = 0.6  # Horizontal offset to appear to the right of the slider

            for dim in range(CATEGORY_DIM):
                article_point_plots[dim].set_data([idx + marker_offset], [art_vec[dim]])
                article_point_plots[dim].set_marker(marker_style)

            for dim in range(METADATA_DIM):
                article_metadata_point_plots[dim].set_data([idx + marker_offset], [art_vec[CATEGORY_DIM + dim]])
                article_metadata_point_plots[dim].set_marker(marker_style)
        else:
            for art_point in article_point_plots:
                art_point.set_data([], [])
            for art_point in article_metadata_point_plots:
                art_point.set_data([], [])

        fig.canvas.draw_idle()

    step_slider.on_changed(update)
    update(0)

    plt.tight_layout()
    plt.show()
    
    print(interaction_display["sum"].describe())