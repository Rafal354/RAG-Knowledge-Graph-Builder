from openai import OpenAI

client = OpenAI()

resp = client.responses.create(
    model="gpt-4o-mini",
    input="hello"
)

print(resp.output[0].content[0].text)
