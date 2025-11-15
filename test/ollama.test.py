import ollama
import sys

# --- Configuration ---
# URL where your Ollama Docker container's API is exposed
OLLAMA_HOST = "http://localhost:11434"
# The name of the model you downloaded inside the Ollama container
MODEL_NAME = "llama3.2"
# A simple prompt to send to the model
PROMPT = """
You are an expert news classifier. Given a news article, your task is to assign a relevance score between 0 and 1 for each of the following 60 categories. Each score should reflect how relevant the article is to that category (0 = not relevant, 1 = highly relevant).

🔒 Your output must meet **ALL** of the following conditions:
- Return a **single flat Python dictionary**.
- The dictionary must contain **exactly 60 keys**, one for each category.
- **Do not omit any key**, even if its value is 0.0.
- **Do not add any extra keys**, text, comments, explanations, or formatting.
- Keys must be the exact category names as listed below.
- Values must be valid Python `float` numbers between 0 and 1 (inclusive).
- Output the dictionary only — no Markdown, no quotes, no code block, no explanation.

📚 These are the categories (grouped for your understanding; output must be flat):

# Topic Categories (30)
Politics, Economy, Sports, Technology, Health, Science, Education, Law_and_Security,
Culture_and_Entertainment, Society, Religion, Environment, International, Infrastructure,
Real_Estate, Military, Crime, Opinion, Consumerism, General_News, Music, Cinema, TV,
Art, Fashion, Food, Travel, History, Family, Animals

# Age Groups (6)
Kids, Teens, Young_Adults, Adults_26_40, Adults_41_60, Seniors

# Content Type (8)
News_Short, Analysis, Opinion_Column, Guide, Recap, Magazine, Interview, Multimedia

# Geographic Scope (4)
Local, Regional, National, Global

# Reading Length (3)
Short, Medium, Long

# Tone (6)
Neutral, Humorous, Emotional, Critical, Informative, Promotional

# Weight (3)
Light, Medium, Heavy

📰 ARTICLE:
\"\"\"
{article_text}
\"\"\"

✏️ OUTPUT (Python dictionary with exactly 60 keys):
"""


# ---

article_text = """ The Israeli military has begun calling up tens of thousands of reservists to "intensify and expand" its operations in Gaza.

The Israel Defense Forces (IDF) said it was "increasing the pressure" with the aim of returning hostages held in Gaza and defeating Hamas militants.

Critics say the recent military offensive, after a ceasefire broke down, has failed to guarantee the release of captives, and question Prime Minister Benjamin Netanyahu's objectives in the conflict.

Under the plan, the military said it would operate in new areas and "destroy all infrastructure" above and below ground.

The Israeli security cabinet is expected to approve a military expansion when it meets on Sunday.

International negotiations have failed to reach a new deal for a ceasefire and the release of the remaining 59 hostages being held by Hamas - 24 of whom are believed to be alive.

No Israeli hostages have been released since Israel resumed its offensive on 18 March after the collapse of a two-month ceasefire with Hamas.

Since then, Israel has seized large areas of Gaza, displacing hundreds of thousands of Gazans again.

Israel has said its aim was to put pressure on Hamas, a strategy that has included a blockade on humanitarian aid that has been in place for more than two months.

Aid agencies, who have reported acute shortages of food, water and medicines, have said this was a policy of starvation that could amount to a war crime, an allegation Israel rejects.

An expanded offensive will put more pressure on exhausted reservists, some of whom have been drafted five or six times since the war started, and renew concerns of the families of hostages, who have urged the government to reach a deal with Hamas, saying this is the only way to save those who are still alive.

The measure will also raise new questions about Netanyahu's real intentions in Gaza.

He has been frequently accused by the hostages' families and opponents of sabotaging negotiations for a deal, and of prolonging the war for political purposes, allegations he denies.

And almost 19 months into the war, he has not presented a day-after plan.

Israeli reservists speak out against Gaza war as pressure on Netanyahu grows
UN's top court begins hearings on Israel's legal duties towards Palestinians
Qatar claims slight progress towards ceasefire in Gaza
The military presented Netanyahu with its planned staged offensive in Gaza on Friday, according to local media.

In recent weeks, thousands of Israeli reservists have signed letters demanding Netanyahu's government stop the fighting and concentrate instead on reaching a deal to bring back the hostages.

On Saturday evening, there were fresh protests across Israel calling for an end to the conflict.

In Tel Aviv, the mother of a hostage who remains in captivity called it a "needless war".

The Israeli military said on Sunday that two more Israeli soldiers had been killed in Gaza.

Earlier on Sunday, a missile fired from Yemen landed near the main terminal of Israel's Ben Gurion airport , Israeli authorities said.

In Gaza, the Hamas-run health ministry said as of 11:05 local time (09:05 BST) on Sunday, 40 people had been killed in the previous 24 hours, and a further 125 injured.

The Israeli military launched a campaign to destroy Hamas in response to an unprecedented cross-border attack on 7 October 2023, in which about 1,200 people were killed and 251 others were taken hostage.

At least 52,535 Palestinians have been killed in Gaza during the ensuing war, according to the territory's Hamas-run health ministry.

Of those, 2,436 have been killed since 18 March, when Israel restarted its offensive in the Gaza Strip, the ministry said. """

print(f"--- Ollama Docker Test Script ---")
print(f"Attempting to connect to Ollama server at: {OLLAMA_HOST}")
print(f"Using model: {MODEL_NAME}")
print("-" * 30)

try:
    # Initialize the client to connect to the specific host
    client = ollama.Client(host=OLLAMA_HOST)

    # 1. Check connection by listing models available on the server
    print("Checking connection by listing models...")
    available_models = client.list()['models']
    model_names = [model['model'] for model in available_models]
    print(f"Found models: {model_names}")

    # Verify the desired model is actually available
    if not any(name.startswith(MODEL_NAME) for name in model_names):
        print(f"\n*** WARNING ***")
        print(f"Model '{MODEL_NAME}' not found on the Ollama server.")
        print(f"Make sure you pulled it inside the container.")
        print(f"Example command: docker exec <your_container_name> ollama pull {MODEL_NAME}")
        print(f"Attempting to use the first available model instead: {model_names[0] if model_names else 'None'}")
        if not model_names:
            print("No models found. Exiting.")
            sys.exit(1)
        # Fallback to the first available model if the desired one isn't there
        actual_model_to_use = model_names[0]
        print(f"Using '{actual_model_to_use}' for the test.")
    else:
        actual_model_to_use = MODEL_NAME
        print(f"Model '{actual_model_to_use}' confirmed available.")

    # 2. Send a request to the chat endpoint
    print(f"\nSending prompt to model '{actual_model_to_use}': '{PROMPT}'")
    response = client.chat(model=actual_model_to_use, messages=[
        {
            'role': 'user',
            'content': PROMPT.format(article_text=article_text),
        },
    ])
    
    # 3. Print the response
    print("\n--- LLM Response ---")
    print(response['message']['content'])
    print("-" * 20)

    print("\nTest completed successfully!")

except Exception as e:
    print(f"\n--- ERROR ---")
    print(f"An error occurred: {e}")
    print("\nTroubleshooting:")
    print(f"- Is the Ollama Docker container running?")
    print(f"- Did you map port 11434 correctly? (e.g., using '-p 11434:11434')")
    print(f"- Did you pull the model '{MODEL_NAME}' (or any model) inside the container?")
    print(f"  (e.g., 'docker exec <container_name> ollama pull {MODEL_NAME}')")
    print(f"- If running this script in another container, is OLLAMA_HOST set correctly (e.g., 'http://ollama:11434')?")
    print("-" * 13)
    sys.exit(1) # Exit with error status