# Gemini API OpenAI-Compatible Mode Examples

## Python Implementation Guide

### 1. Basic Chat Completion
```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain how AI works"}
    ]
)
print(response.choices[0].message)
```

**Key Points**:
- Uses standard OpenAI client format
- Requires setting `base_url` to Gemini's endpoint
- Works with standard chat completion parameters

[... rest of content ...]
