import numpy as np
from utils import * 
from article import Article
import matplotlib.pyplot as plt
from rich import print
import pandas as pd
from scipy.stats import pearsonr


#####################################################################################################################################
##                                                                  PLOTING                                                        ##
#####################################################################################################################################
def plot_learning():
    '''
    '''   
    n_users = len(users)

    fig, axes = plt.subplots(n_users, 1, figsize=(12, 4 * n_users), sharex=True)

    for ax, user, history, updates in zip(axes, users, all_histories, all_updates):
        for dim in range(CATEGORY_DIM):
            ax.plot(history[:, dim], label=categories[dim])
        ax.set_title(user['name'])
        ax.set_ylabel('Interest Value')
        ax.set_ylim(0,1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1))

    # Shared x-axis labels on bottom subplot
    axes[-1].set_xticks(range(len(all_updates[0])))
    axes[-1].set_xticklabels([update.split(":")[0] for update in all_updates[0]], rotation=45, ha='right')
    axes[-1].set_xlabel('Update Step')

    plt.tight_layout()
    plt.show()


def plot_per_cat():
    # --- Plot per-category article value distributions and user's interest vector ---
    n_users = len(users)
    n_categories = CATEGORY_DIM

    # Each user's data is a column: (n_categories + 1) rows, n_users columns
    fig, axes = plt.subplots(n_categories + 1, n_users, figsize=(5 * n_users, 2.5 * (n_categories + 1)), sharex='col')

    # If only one user, axes is 1D, make it 2D for consistency
    if n_users == 1:
        axes = np.expand_dims(axes, axis=1)

    for user_idx, user in enumerate(users):
        seen_articles = engagment_history[user["name"]]
        if not seen_articles:
            continue

        # Gather article vectors for seen articles
        article_vectors = np.array([article.get_vector() for article in seen_articles])
        # User's final interest vector
        user_interest_vec = all_histories[user_idx][-1]

        # For each category, plot the distribution of values across seen articles
        for idx, cat in enumerate(categories):
            cat_values = article_vectors[:, idx] if article_vectors.shape[0] > 0 else np.array([])
            ax = axes[idx, user_idx] if n_users > 1 else axes[idx, 0]
            ax.hist(cat_values, bins=20, color='skyblue', edgecolor='black', range=(0,1))
            ax.set_ylabel(f'"{cat}"\nCount')
            ax.set_xlim(-0.05,1.05)  # Make the plot wider to show all values
            ax.set_xticks(np.linspace(0, 1, 11))
            ax.set_xticklabels([f"{x:.1f}" for x in np.linspace(0, 1, 11)])
            ax.set_ylim(bottom = 0)
            if user_idx == 0:
                ax.set_title(f'Distribution of "{cat}" values')
            if idx == n_categories - 1:
                ax.set_xlabel('Value')

        # Last subplot: user's interest vector as a bar plot
        ax_interest = axes[-1, user_idx] if n_users > 1 else axes[-1, 0]
        bar_positions = np.arange(CATEGORY_DIM)
        ax_interest.bar(bar_positions, user_interest_vec, color='orange')
        ax_interest.set_xticks(bar_positions)
        ax_interest.set_xticklabels(categories, rotation=45, ha='right')
        ax_interest.set_ylabel('Interest Value')
        ax_interest.set_ylim(0, 1)
        ax_interest.set_title(f"{user['name']}'s Interest Vector")

    plt.tight_layout()
    plt.show()

#####################################################################################################################################
##                                                              Category Setup                                                     ##
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
##                                                     Demographic influence weights                                               ##
#####################################################################################################################################
DEMOGRAPHIC_INFLUENCES = {
    'age': {
        (0, 17):   {'Culture & Entertainment': 0.15, 'Science & Technology': 0.10, 'Sports': 0.05},
        (18, 24):  {'Culture & Entertainment': 0.10, 'Science & Technology': 0.10, 'Sports': 0.05},
        (25, 34):  {'Science & Technology': 0.10, 'Economy & Business': 0.07, 'Culture & Entertainment': 0.05},
        (35, 49):  {'Health & Wellness': 0.10, 'Education & Society': 0.07, 'Opinion & General News': 0.05},
        (50, 64):  {'Health & Wellness': 0.12, 'Opinion & General News': 0.10},
        (65, 100): {'Health & Wellness': 0.15, 'Opinion & General News': 0.10},
    },
    'gender': {
        'female':      {'Health & Wellness': 0.08, 'Opinion & General News': 0.05},
        'male':        {'Sports': 0.08, 'Science & Technology': 0.05},
        'unknown':     {}
    },
    'location': {
        'urban':    {'Politics & Law': 0.10, 'World & International Affairs': 0.10, 'Economy & Business': 0.05},
        'suburban': {'Education & Society': 0.10, 'Culture & Entertainment': 0.05},
        'rural':    {'Economy & Business': 0.10, 'Education & Society': 0.05},
        'unknown':  {}
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

#####################################################################################################################################
##                                                         Vector initialzation                                                    ##
#####################################################################################################################################
def initialize_user_vector(preferences, age, gender, location, base=0.5):
    """
    Start with base (e.g., 0.5) and adjust with demographics and preferences.
    """
    vec = np.ones(CATEGORY_DIM) * base # Initialize all categories interest to 0.5

    log_updates(vec,"Init",interest_vectors_history, interest_vectors_updates)

    # Apply demographics to update interest vector
    vec += encode_demographics(age, gender, location)
    vec = rescale_and_normalize_vector(vec, TARGET_SUM)
    log_updates(vec,"Demographics",interest_vectors_history, interest_vectors_updates)

    # Apply preference boost
    for pref in preferences:
        if pref in category_to_index:
            vec[category_to_index[pref]] += 0.25   # override to strong interest


    vec = rescale_and_normalize_vector(vec)
    log_updates(vec, "Preferences", interest_vectors_history, interest_vectors_updates)
    return vec

def is_liked(prob: float) -> bool:
    """
    Decide if liked based on probability.
    """
    return np.random.rand() < prob


#####################################################################################################################################
##                                                         --- Vector Update ---                                                   ##
##################################################################################################################################### 
def update_user_vector(user_vector: np.array, article: Article, step=None, learning_rate=0.05):
    """
    Update the user vector with decay for each engagement.
    """
    global liked_count
    global disliked_count
    vec = np.array(user_vector)
    median = np.median(vec)
    art_vec = np.array(article.get_vector())
    sim = article.get_sim()
    
    # # *Pearson correlation with cosine similarity
    # corr_like_prob = pearsonr(vec, art_vec).statistic
    # like_prob = corr_like_prob
    
    # # *KL-Divergence as similarity
    # kl_divergenece_like_prob = np.exp(-3.0 * sim)    
    # like_prob = kl_divergenece_like_prob
    
    # *Median deviation shape similarity
    sigmoid_like_prob = sigmoid(sim)        
    like_prob = sigmoid_like_prob
    
    if is_liked(like_prob):
        liked_count += 1
        
        # !Rocchio 
        # updated_vec = update_rocchio(vec, liked_vecs=[art_vec], disliked_vecs=None)
        
        # !Naive approach 1
        # updated_vec = np.array([ val + learning_rate * abs(val - median) if val >= median else val - learning_rate * abs(val - median) for val in vec ])
        
        # !Naive approach 2
        # delta = art_vec - median
        # delta_norm = delta / np.max(delta)
        # updated_vec = vec + learning_rate * delta_norm
        
        # !Article median distance based update
        update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in art_vec])
        updated_vec = np.array([val + learning_rate * update_ratio[i] if art_vec[i] >= median else val - learning_rate * update_ratio[i] for i, val in enumerate(vec)])
    
    else:
        disliked_count += 1
        
        # !Rocchio 
        # updated_vec = update_rocchio(vec, liked_vecs=None, disliked_vecs=[art_vec])
        
        # !Naive approach 1
        # updated_vec = np.array([ val - (learning_rate * abs(val - median)) if val >= median else val - (learning_rate * abs(val - median)) for val in vec ])
        
        # !Naive approach 2
        # delta = art_vec - median
        # delta_norm = delta / np.max(delta)
        # updated_vec = vec - learning_rate * delta_norm
                
        # !Article median distance based update
        update_ratio =  np.array([1 - (art_val / median) if art_val <= median else 1 - (median / art_val) for art_val in art_vec]) 
        updated_vec = np.array([val - learning_rate * update_ratio[i] if art_vec[i] >= median else val + learning_rate * update_ratio[i] for i, val in enumerate(vec)])

    updated_vec = rescale_and_normalize_vector(updated_vec)

    log_updates(updated_vec, f"Engagement Step {step}: {article.get_category()}", interest_vectors_history, interest_vectors_updates)

    return updated_vec


def update_rocchio(user_vec, liked_vecs=None, disliked_vecs=None,
                   alpha=0.8, beta=0.2, gamma=0.2):
    """
    Rocchio update: combine old profile with positive/negative feedback.
    """
    p = alpha * user_vec
    if liked_vecs != None:
        p += (beta / len(liked_vecs)) * np.sum(liked_vecs, axis=0)
    if disliked_vecs != None:
        p -= (gamma / len(disliked_vecs)) * np.sum(disliked_vecs, axis=0)
    # enforce non-negativity
    p = np.clip(p, 0, None)
    # renormalize to sum = TARGET_SUM
    return p * (TARGET_SUM / p.sum())

# --- User Simulation ---
def simulate_user_engagement(preferences: list[str], engagements: list, age: int, gender: str, location: str, learning_rate: float=0.05 , decay: float=0.05):
    """
    Simulate user interest vector evolution given preferences, demographics, and engagements.
    """
    user_vector = initialize_user_vector(preferences, age, gender, location)
    user["vector"] = user_vector

    # engagements = list(engagements.items())
    # random.shuffle(engagements)

    # for step, engagement in enumerate(engagements, start=1):
    #     user_vector = update_user_vector(user_vector, engagement, step, 0.15, None)

    for step in range(0,40):
        article = get_article_for_user(user_vector)
        engagment_history[user["name"]].append(article)
        
        new_vec = update_user_vector(user["vector"], article=article, step=step)
        delta = new_vec - user_vector
        user["vector"] = new_vec
        interaction.loc[len(interaction)] = [user["name"] ,step, round(article.get_sim(), 2), article.get_vector(), user_vector, delta]
        
    return

def order_articles_for_user(user_vec : np.array)-> list[Article]:
    for article in articles:
        # article.set_sim(kl_divergence(article.get_vector(),user_vec))  # KL divergence
        article.set_sim(median_deviation_shape_similarity(article.get_vector(),user_vec))  # Median deviation shape
        # article.set_sim(cos_similarity(user_vec, article.get_vector()))  # Cosine similarity
        
    articles.sort(key=lambda article: article.get_sim(), reverse=True)
    return articles

def get_article_for_user(user_vec: np.array)-> Article:
    ordered_articles = order_articles_for_user(user_vec)
    num_of_article_pool = 10
    article = np.random.choice(ordered_articles[:num_of_article_pool], p=[1/num_of_article_pool for i in range(num_of_article_pool)])
    ordered_articles.remove(article)
    return article



# ---- EXAMPLE ----
if __name__ == "__main__":
    interaction = pd.DataFrame(columns=["user" ,"step","similarity","article vector", "user vector","vector update"])
    all_histories = []
    all_updates = []
    interest_vectors_history = []
    interest_vectors_updates = []
    users = load_users()
    engagment_history = {user["name"]:[] for user in users}

    # Simulate and print each user's interest vector evolution
    for user in users:
        liked_count = 0
        disliked_count = 0
        articles = load_article_vectors()
        interest_vectors_history.clear()
        interest_vectors_updates.clear()
        simulate_user_engagement(
            user['preferences'],
            user['engagements'],
            user['age'],
            user['gender'],
            user['location']
        )
        all_histories.append(np.array(interest_vectors_history))
        all_updates.append(list(interest_vectors_updates))
        print_likes(liked_count, disliked_count)
        print(f"\n--- {user['name']}'s engagement trace ---")
        for step, vec in zip(interest_vectors_updates, interest_vectors_history):
            print(f"{step}: {np.round(vec, 3)} (sum = {vec.sum():.3f})")

        # print_deltas()

    print(interaction.head(20))
    plot_learning()
    # plot_per_cat()
