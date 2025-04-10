"""
Utility functions to call a Large Language Model (LLM) API.
Provides both standard calls and structured output capabilities.
"""
import os
import time
import json
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI
from openai import OpenAIError
import logging

def call_llm(prompt, model="gpt-4o", temperature=0.7, max_tokens=1000, timeout=60):
    """
    Calls an LLM API with the given prompt and returns the response.
    
    Args:
        prompt (str): The prompt to send to the LLM
        model (str): The model to use (default: gpt-4o)
        temperature (float): Controls randomness (0.0-1.0)
        max_tokens (int): Maximum number of tokens to generate
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        str: The LLM's response
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return "Error: OpenAI API key not found in environment variables."
    
    # Log API key first few and last few characters for debugging
    masked_key = f"{api_key[:5]}...{api_key[-5:]}"
    logging.debug(f"Using API key: {masked_key}")
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(
            api_key=api_key
        )
        
        # Make the API call with proper timeout handling
        start_time = time.time()
        logging.debug(f"Starting OpenAI API call to model {model}")
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI API call completed in {elapsed:.2f} seconds")
            
            # Extract and return the response content
            content = response.choices[0].message.content
            logging.debug(f"Received response of length {len(content)} characters")
            return content
            
        except Exception as api_error:
            elapsed = time.time() - start_time
            logging.error(f"OpenAI API error after {elapsed:.2f} seconds: {str(api_error)}")
            
            # Handle specific error types
            error_message = str(api_error).lower()
            if "timeout" in error_message:
                return f"Error: LLM API call timed out after {elapsed:.1f} seconds."
            elif "rate limit" in error_message:
                return "Error: Rate limit exceeded. Please try again later."
            elif "invalid auth" in error_message or "authentication" in error_message:
                return "Error: Authentication failed. Please check your API key."
            else:
                return f"Error calling LLM API: {str(api_error)}"
                
    except Exception as e:
        logging.exception("Unexpected error initializing OpenAI client")
        return f"Error initializing OpenAI client: {str(e)}"


def call_llm_structured(schema: Dict[str, Any], 
                    system_prompt: str = None,
                    user_prompt: str = None,
                    messages: List[Dict[str, str]] = None,
                    model: str = "gpt-4o", 
                    temperature: float = 0.7, 
                    timeout: int = 60) -> Dict[str, Any]:
    """
    Calls an LLM API with structured output capabilities using the OpenAI Responses API.
    
    Args:
        schema (Dict[str, Any]): JSON schema defining the structure of the expected output
        system_prompt (str, optional): System prompt to set context for the model
        user_prompt (str, optional): User prompt for the request
        messages (List[Dict[str, str]], optional): Full message history if needed instead of simple prompts
        model (str): The model to use (default: gpt-4o)
        temperature (float): Controls randomness (0.0-1.0)
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        Dict[str, Any]: Structured response following the provided schema
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return {"error": "OpenAI API key not found in environment variables."}
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(
            api_key=api_key
        )
        
        # Prepare messages if not provided directly
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})
        
        # Make sure we have at least one message
        if not messages:
            logging.error("No messages provided for structured output call")
            return {"error": "No messages provided for the API call."}
        
        # Make the API call with proper timeout handling
        start_time = time.time()
        logging.debug(f"Starting OpenAI Responses API call to model {model} with structured output")
        
        try:
            response = client.responses.create(
                model=model,
                input=messages,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "structured_output",
                        "schema": schema,
                        "strict": True
                    }
                },
                temperature=temperature,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI Responses API call completed in {elapsed:.2f} seconds")
            
            # Parse and return the JSON response
            try:
                structured_output = json.loads(response.output_text)
                logging.debug(f"Successfully parsed structured response")
                return structured_output
            except json.JSONDecodeError as json_err:
                logging.error(f"Failed to parse JSON response: {str(json_err)}")
                return {"error": f"Failed to parse JSON response: {str(json_err)}"}
            
        except Exception as api_error:
            elapsed = time.time() - start_time
            logging.error(f"OpenAI API error after {elapsed:.2f} seconds: {str(api_error)}")
            
            # Handle specific error types
            error_message = str(api_error).lower()
            if "timeout" in error_message:
                return {"error": f"LLM API call timed out after {elapsed:.1f} seconds."}
            elif "rate limit" in error_message:
                return {"error": "Rate limit exceeded. Please try again later."}
            elif "invalid auth" in error_message or "authentication" in error_message:
                return {"error": "Authentication failed. Please check your API key."}
            else:
                return {"error": f"Error calling LLM API: {str(api_error)}"}
                
    except Exception as e:
        logging.exception("Unexpected error initializing OpenAI client")
        return {"error": f"Error initializing OpenAI client: {str(e)}"}


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Test the standard call_llm function
    test_prompt = "Explain what a YouTube video summarizer does in one sentence."
    print("1. Testing standard call_llm function...")
    response = call_llm(test_prompt, max_tokens=100)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")
    
    # Test the structured output function
    print("\n2. Testing call_llm_structured function...")
    schema = {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
                "description": "An explanation of what a YouTube video summarizer does"
            },
            "key_features": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Key features of a YouTube video summarizer"
            }
        },
        "required": ["explanation", "key_features"],
        "additionalProperties": False
    }
    
    structured_response = call_llm_structured(
        schema=schema,
        system_prompt="You are a helpful assistant that explains YouTube tools.",
        user_prompt="Explain what a YouTube video summarizer does and list its key features.",
        temperature=0.5
    )
    
    print("Schema:", json.dumps(schema, indent=2))
    print("Structured Response:", json.dumps(structured_response, indent=2))
