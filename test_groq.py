
import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": "You are a structured data extraction assistant. Return valid JSON only."
        },
        {
            "role": "user",
            "content": """
            Extract the following information:

            Company: OpenAI
            Product: ChatGPT
            Category: Generative AI

            Return JSON with these fields:
            company, product, category.
            """
        }
    ],
    response_format={"type": "json_object"},
    temperature=0,
    max_completion_tokens=300
)

result = json.loads(response.choices[0].message.content)

print("\nGROQ MODEL TEST SUCCESSFUL")
print(json.dumps(result, indent=2))
