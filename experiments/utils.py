import json
import numpy as np
from article import Article
from numpy.linalg import norm
from scipy.special import rel_entr

TARGET_SUM = 5

def log_updates(vec, step, interest_vectors_history, interest_vectors_updates):
    # vec = np.array(vec)
    interest_vectors_history.append(vec.copy())
    interest_vectors_updates.append(step)
# articles_normalized_new
def load_article_vectors(json_path: str = 'articles_normalized_new.json') -> list[Article]:
    """
    Reads the JSON file and returns a dict mapping
    article titles to their 10-dim interest vectors.
    """
    with open(json_path, 'r') as f:
        articles = json.load(f)
    
    article_arr = []
    for item in articles["articles"]:
        vector = item["categories"]
        desc = item["description"]
        article_arr.append(Article(desc,vector))
        
    return article_arr

def load_users(json_path: str = 'users.json') -> list[dict]:
    """
    Reads the JSON file and returns a dict of users.
    """
    with open(json_path, 'r') as f:
        users = json.load(f)
    return users


def cos_similarity(vector_a: np.array ,  vector_b: np.array ) -> float:
    """
    Calculate Cosine similarity between two vectors.
    """
    if np.array(vector_a).ndim != np.array(vector_b).ndim:
        raise ArithmeticError("Vectors should have same dimensions.")
    cos_sim = np.dot(vector_a, vector_b)/(norm(vector_a)*norm(vector_b))
    return cos_sim


def kl_divergence(vector_a: np.array ,  vector_b: np.array, epsilon: float = 1e-10 ) -> float:
    if np.array(vector_a).ndim != np.array(vector_b).ndim:
        raise ArithmeticError("Vectors should have same dimensions.")
    sum_a = np.sum(vector_a)
    sum_b = np.sum(vector_b)
    norm_a = [val / sum_a for val in vector_a]
    norm_b = [val / sum_b for val in vector_b]
    norm_a = np.clip(norm_a, epsilon, 1)
    norm_b = np.clip(norm_b, epsilon, 1)
    return sum(rel_entr(norm_a, norm_b))


def median_deviation_shape_similarity(user, article):

    user = np.array(user, dtype=np.float64)
    article = np.array(article, dtype=np.float64)

    # Step 1: subtract median (centering)
    user_dev = user - np.median(user)
    article_dev = article - np.median(article)

    # Step 2: normalize to unit scale (optional but good)
    user_norm = user_dev / (np.linalg.norm(user_dev) + 1e-10)
    article_norm = article_dev / (np.linalg.norm(article_dev) + 1e-10)

    # Step 3: measure similarity via dot product (same as cosine on centered vectors)
    similarity = np.dot(user_norm, article_norm)

    return similarity  # Range ~ [-1, 1]

def sigmoid(sim, sharpness=5.0)-> float:
    return 1 / ( 1 + np.exp( -sharpness * sim))

def rescale_and_normalize_vector(vector: np.array , target_sum=TARGET_SUM) -> np.array:
    min_val = np.min(vector)
    
    if min_val < 0:
       vector += np.abs(min_val)

    sum = np.abs(vector).sum()
    vector *= (target_sum/sum)
 
    return vector
     
def print_deltas(interest_vectors_history: list[np.array]) -> None:
    print("Deltas:")
    print(f"Change from start to demographics: {np.round(interest_vectors_history[1] - interest_vectors_history[0], 3)}")
    print(f"Change from demographics to preferences: {np.round(interest_vectors_history[2] - interest_vectors_history[1],3)}")
    print(f"Change from preferences to 1st step: {np.round(interest_vectors_history[3] - interest_vectors_history[2],3)}")
    print(f"Change from 1st step to last step: {np.round(interest_vectors_history[-1] - interest_vectors_history[3],3)}")
    
def print_likes(liked: int, disliked: int) -> None:
    if liked and disliked:
        print(f"Liked: {liked}")
        print(f"Disliked: {disliked}")