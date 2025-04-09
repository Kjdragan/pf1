"""
Utility function to call a Large Language Model (LLM) API.
"""
import os
import time
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


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Test the function with a simple prompt
    test_prompt = "Explain what a YouTube video summarizer does in one sentence."
    
    print("Testing call_llm function...")
    response = call_llm(test_prompt, max_tokens=100)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")
