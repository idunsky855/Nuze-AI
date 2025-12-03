import math

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

METADATA_KEYS = [
    "Length",
    "Complexity",
    "Tone",
    "Content_type",
    "Named Entities",
]

ALLOWED_CONTENT_TYPES = [
    "News", "Analysis", "Opinion", "Interview",
    "Guide", "Recap", "Multimedia"
]

TONE_KEYS = ["Neutral", "Informative", "Emotional"]


def validate_output(result: dict):
    """
    Validate an LLM classification output according to strict rules.
    Returns: (bool, error_message)
    """
    # -----------------------------
    # 1. Correct type
    # -----------------------------
    if not isinstance(result, dict):
        return False, "Output is not a Python dictionary."

    # -----------------------------
    # 2. Top-level key count
    # -----------------------------
    if len(result) != 15:
        return False, f"Dictionary must contain exactly 15 keys, found {len(result)}."

    # -----------------------------
    # 3. Check presence of all category keys
    # -----------------------------
    for cat in CATEGORIES:
        if cat not in result:
            return False, f"Missing category key: '{cat}'."
        if not isinstance(result[cat], (int, float)):
            return False, f"Value for category '{cat}' must be a number."
        if not (0 <= float(result[cat]) <= 5):
            return False, f"Value for '{cat}' must be between 0 and 5."

    # -----------------------------
    # 4. Category scores sum to exactly 5.0
    # -----------------------------
    total = sum(float(result[cat]) for cat in CATEGORIES)

    # If the total is not exactly 5.0, perform a normalization step to adjust values
    # into a set that sums to exactly 5.0 (rounding to 4 decimals and fixing remainder
    # by adding/subtracting the tiny remainder to the largest value). This mutates
    # the `result` dict in-place so callers receive the corrected scores.
    if not math.isclose(total, 5.0, abs_tol=1e-6):
        if total <= 0:
            return False, f"Category scores must sum to 5.0, but sum is {total}."

        # Normalize raw scores to sum to 5.0
        normalized = {}
        for cat in CATEGORIES:
            raw = float(result[cat])
            normalized[cat] = round(5.0 * (raw / total), 4)

        # Fix any rounding remainder by adjusting the largest value
        rounded_total = sum(normalized.values())
        remainder = round(5.0 - rounded_total, 4)
        if abs(remainder) >= 1e-12:
            # choose the category with the largest normalized value to absorb the remainder
            max_cat = max(CATEGORIES, key=lambda c: normalized[c])
            normalized[max_cat] = round(normalized[max_cat] + remainder, 4)

        # write back into result
        for cat in CATEGORIES:
            result[cat] = float(normalized[cat])

        # recompute total for reporting/validation
        total = sum(float(result[cat]) for cat in CATEGORIES)
        if not math.isclose(total, 5.0, abs_tol=1e-6):
            return False, f"Category scores must sum to 5.0 after normalization, but sum is {total}."

    # -----------------------------
    # 5. Check metadata keys exist
    # -----------------------------
    for key in METADATA_KEYS:
        if key not in result:
            return False, f"Missing metadata key: '{key}'."

    # -----------------------------
    # 6. Length & Complexity
    # -----------------------------
    if not isinstance(result["Length"], (int, float)) or not (0 <= result["Length"] <= 1):
        return False, "Length must be a float between 0 and 1."

    if not isinstance(result["Complexity"], (int, float)) or not (0 <= result["Complexity"] <= 1):
        return False, "Complexity must be a float between 0 and 1."

    # -----------------------------
    # 7. Tone validation
    # -----------------------------
    tone = result["Tone"]
    if not isinstance(tone, dict):
        return False, "Tone must be a dictionary."

    if set(tone.keys()) != set(TONE_KEYS):
        return False, f"Tone must contain exactly {TONE_KEYS}."

    for tk in TONE_KEYS:
        if not isinstance(tone[tk], (int, float)) or not (0 <= tone[tk] <= 1):
            return False, f"Tone['{tk}'] must be a float between 0 and 1."

    # -----------------------------
    # 8. Content_type validation
    # -----------------------------
    if result["Content_type"] not in ALLOWED_CONTENT_TYPES:
        return False, f"Content_type must be one of {ALLOWED_CONTENT_TYPES}."

    # -----------------------------
    # 9. Named Entities validation
    # -----------------------------
    entities = result["Named Entities"]
    if not isinstance(entities, list):
        return False, "Named Entities must be a list of strings."

    if any(not isinstance(e, str) for e in entities):
        return False, "Each Named Entity must be a string."

    # -----------------------------
    # 10. Ensure no unknown keys
    # -----------------------------
    expected_keys = set(CATEGORIES) | set(METADATA_KEYS)
    extra = set(result.keys()) - expected_keys
    if extra:
        return False, f"Unexpected keys found: {extra}"

    # -----------------------------
    # All checks passed
    # -----------------------------
    return True, None
