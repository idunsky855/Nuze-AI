import ollama
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.llm_validator import validate_output

OLLAMA_HOST = "http://ollama:11434"
MODEL_NAME = "news-classifier"

PROMPT = """Analyze the following article and return the JSON object:
{article_text}
"""


article_text = """The Israeli military has begun calling up tens of thousands of reservists to "intensify and expand" its operations in Gaza.

The Israel Defense Forces (IDF) said it was "increasing the pressure" with the aim of returning hostages held in Gaza and defeating Hamas militants.

Critics say the recent military offensive, after a ceasefire broke down, has failed to guarantee the release of captives, and question Prime Minister Benjamin Netanyahu's objectives in the conflict.

Under the plan, the military said it would operate in new areas and "destroy all infrastructure" above and below ground.

The Israeli security cabinet is expected to approve a military expansion when it meets on Sunday.

International negotiations have failed to reach a new deal for a ceasefire and the release of the remaining 59 hostages being held by Hamas - 24 of whom are believed to be alive.

No Israeli hostages have been released since Israel resumed its offensive on 18 March after the collapse of a two-month ceasefire with Hamas.

Since then, Israel has seized large areas of Gaza, displacing hundreds of thousands of Gazans again.

Israel has said its aim was to put pressure on Hamas, a strategy that has included a blockade on humanitarian aid that has been in place for more than two months.

Aid agencies, who have reported acute shortages of food, water and medicines, have said this was a policy of starvation that could amount to a war crime, an allegation Israel rejects."""

try:
    print("=== Ollama Test Script ===")
    print(f"Model: {MODEL_NAME}")
    print(f"Host: {OLLAMA_HOST}\n")

    client = ollama.Client(host=OLLAMA_HOST)
    
    # Verify model exists
    models = client.list()
    model_names = [m.model for m in models.models]
    print(f"Available models: {model_names}")
    
    if MODEL_NAME not in model_names and MODEL_NAME + ":latest" not in model_names:
        print(f"ERROR: Model '{MODEL_NAME}' not found!")
        exit(1)
    
    print(f"Using model: {MODEL_NAME}\n")

    # Send prompt
    prompt_filled = PROMPT.replace("{article_text}", article_text)
    
    print("Sending prompt to model...")
    start_time = time.time()
    response = client.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt_filled}],
        stream=False
    )
    total_time = time.time() - start_time
    print('-'*40, '\n')
    print(f'Interaction took: {total_time} Seconds\n')
    print('-'*40, '\n')
    raw_response = response.message.content
    print("\n--- Raw Response ---")
    print(raw_response[:200] + "..." if len(raw_response) > 200 else raw_response)
    print("--------------------\n")
    
    # Strip markdown code blocks and extra text
    cleaned = raw_response.strip()
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    
    # Parse JSON
    result = json.loads(cleaned)
    
    # Handle nested "category" dictionary if present
    if "category" in result and isinstance(result["category"], dict):
        print("⚠ Found nested 'category' dictionary, flattening...")
        for k, v in result["category"].items():
            result[k] = v
        del result["category"]

    # Normalize key names
    if "Named_Entities" in result:
        result["Named Entities"] = result.pop("Named_Entities")
    
    print("✓ Successfully parsed JSON")
    print(f"Keys: {list(result.keys())}\n")
    
    # Define categories explicitly
    categories = [
        "Politics & Law", "Economy & Business", "Science & Technology",
        "Health & Wellness", "Education & Society", "Culture & Entertainment",
        "Religion & Belief", "Sports", "World & International Affairs",
        "Opinion & General News"
    ]
    
    # Normalize category scores if needed
    cat_scores = [result.get(k, 0) for k in categories]
    total = sum(cat_scores)
    
    if abs(total - 5.0) > 0.01:  # If not close to 5.0
        print(f"\n⚠ Category sum is {total}, normalizing to 5.0...")
        if total > 0:
            for k in categories:
                # Update only if key exists or if we want to force it
                if k in result or result.get(k, 0) > 0:
                    result[k] = round(result.get(k, 0) * 5.0 / total, 2)
        # Verify after normalization
        new_total = sum(result.get(k, 0) for k in categories)
        print(f"After normalization: {new_total}")
    
    # Validate
    is_valid, error_msg = validate_output(result)
    if is_valid:
        print("✓ VALIDATION PASSED!")
        print(json.dumps(result, indent=2))
    else:
        print(f"✗ Validation failed:")
        print(f"  - {error_msg}")
        
        # Show category scores
        # Re-calculate total based on explicit categories to avoid TypeErrors with unexpected keys
        total = sum(result.get(k, 0) for k in categories)
        print(f"\nCategory scores sum: {total} (need 5.0)")
        print("Scores:")
        for k in categories:
            print(f"  {k}: {result.get(k, 0)}")

except json.JSONDecodeError as e:
    print(f"✗ Failed to parse JSON: {e}")
    print("Response was:")
    print(raw_response)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
