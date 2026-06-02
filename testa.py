from anthropic import AnthropicVertex

client = AnthropicVertex(region="global", project_id="YOUR_PROJECT_ID")
message = client.messages.create(
 max_tokens=1024,
 messages=[{"role": "user", "content": "Hello! Can you help me?"}],
 model="claude-opus-4-8"
)
print(message.content[0].text)