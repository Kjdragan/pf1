"""
Utility function to call a Large Language Model (LLM) API.
"""
import os
import time
from openai import OpenAI

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
        return "Error: OpenAI API key not found in environment variables."
    
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key, timeout=timeout)
        
        # Set start time for timeout tracking
        start_time = time.time()
        
        # Call the API with timeout
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Check if we've exceeded our timeout
        if time.time() - start_time > timeout:
            return f"Error: LLM API call timed out after {timeout} seconds."
        
        # Extract and return the response text
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error calling LLM API: {str(e)}"


if __name__ == "__main__":
    # Test the function with a simple prompt
    test_prompt = "Explain what a YouTube video summarizer does in one sentence."
    
    # Note: This will only work if you have set the OPENAI_API_KEY environment variable
    response = call_llm(test_prompt, max_tokens=100)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")
