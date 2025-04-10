# OpenAI API Best Practices

## Using Structured Outputs with OpenAI

### Benefits of Structured Outputs
- **Reliable type-safety**: No need to validate or retry incorrectly formatted responses
- **Explicit refusals**: Safety-based model refusals are now programmatically detectable
- **Simpler prompting**: No need for strongly worded prompts to achieve consistent formatting

### Implementation Guide

#### Basic Implementation with the Responses API

```python
from openai import OpenAI
import json

client = OpenAI()

response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": "Extract the information."},
        {"role": "user", "content": "The content to extract information from"}
    ],
    text={
        "format": {
            "type": "json_schema",
            "name": "schema_name",
            "schema": {
                "type": "object",
                "properties": {
                    "property1": {
                        "type": "string"
                    },
                    "property2": {
                        "type": "array", 
                        "items": {
                            "type": "string"
                        }
                    },
                },
                "required": ["property1", "property2"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
)

result = json.loads(response.output_text)
```

#### Using with Pydantic Models

For better code organization and type safety:

```python
from pydantic import BaseModel, Field
from openai import OpenAI
import json
from typing import List

# Define your Pydantic model
class YourModel(BaseModel):
    property1: str = Field(..., description="Description of this property")
    property2: List[str] = Field(..., description="Description of this list property")

# Initialize OpenAI client
client = OpenAI()

# Create the schema from your model
schema = {
    "type": "object",
    "properties": {
        "property1": {
            "type": "string",
            "description": "Description of this property"
        },
        "property2": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Description of this list property"
        }
    },
    "required": ["property1", "property2"],
    "additionalProperties": False
}

# Use the schema in your API call
response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": "Your system instruction"},
        {"role": "user", "content": "User query"}
    ],
    text={
        "format": {
            "type": "json_schema",
            "name": "your_model",
            "schema": schema,
            "strict": True
        }
    }
)

# Parse the result
result = json.loads(response.output_text)
```

### Supported Models
- gpt-4.5-preview-2025-02-27 and later
- o3-mini-2025-1-31 and later
- o1-2024-12-17 and later
- gpt-4o-mini-2024-07-18 and later
- gpt-4o-2024-08-06 and later

### Best Practices
1. **Always validate responses**: Even with structured outputs, validate the content for domain-specific logic
2. **Handle refusals gracefully**: Check for the `refusal` property in the response
3. **Keep schemas concise**: Focus on the essential properties you need
4. **Set appropriate fields as required**: All fields in structured outputs must be specified as required
5. **Use proper typing**: Match your schema types to what you expect in the response
6. **Error handling**: Always include robust error handling for API calls

### When to Use
- Use structured outputs when you need consistent, predictable response formats
- Perfect for extracting specific information from text
- Ideal for creating Q&A pairs, taxonomies, or structured analysis
- Use for any application where parsing JSON response data is required

### JSON Schema Limitations
- A schema may have up to 100 object properties total, with up to 5 levels of nesting
- Total string length of all property names, definition names, enum values, and const values cannot exceed 15,000 characters
- A schema may have up to 500 enum values across all enum properties
- Must set `additionalProperties: false` in objects
