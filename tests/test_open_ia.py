import os

from dotenv import load_dotenv
from openai import OpenAI

# load_dotenv()

print("WORKDIR =", os.getcwd())
print("LOADED KEY:", os.getenv("OPENAI_API_KEY"))

client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"hello"}]
)
print(resp.choices[0].message.content)
