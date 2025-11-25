import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# load_dotenv()
print("ENV KEY SEEN BY PYTHON:", os.getenv("OPENAI_API_KEY"))

llm = init_chat_model("gpt-4o-mini")
resp = llm.invoke([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is temperature of boiling water?"}
])

print("MODEL RESPONSE:", resp.content)
