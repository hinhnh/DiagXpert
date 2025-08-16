import openai

client = openai.OpenAI(
    base_url="https://aiportalapi.stu-platform.live/jpe",
    api_key="sk-eYXKyPpMtssHMByifvqR2Q"
)

response = client.chat.completions.create(
    model="GPT-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)