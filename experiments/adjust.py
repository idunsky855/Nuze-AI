import json

# 1) Load your JSON (from a file or a string)
with open('articles.json', 'r') as f:
    data = json.load(f)

# 2) Divide every category value by 5.0 to bring them into [0,1]
for article in data['articles']:
    article['categories'] = [x / 5.0 for x in article['categories']]

# 3) (Optional) Write the normalized JSON back out
with open('articles_normalized_new.json', 'w') as f:
    json.dump(data, f, indent=2)

# 4) Or just print it:
print(json.dumps(data, indent=2))