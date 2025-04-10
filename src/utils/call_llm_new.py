"""
Utility functions to call a Large Language Model (LLM) API.
Provides both standard calls and structured output capabilities with optimizations for prompt caching.
"""
import os
import time
import json
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI
from openai import OpenAIError
import logging

# Import the cost calculation utility
from .calculate_llm_costs import global_metrics
# Import token scaling utility
from .token_scaling import calculate_max_tokens

def create_cacheable_prompt(static_instructions: str, dynamic_content: str) -> str:
    """
    Structures a prompt to optimize for OpenAI's caching mechanism.
    Places static content first (which can be cached) followed by dynamic content.
    
    For prompt caching to work effectively:
    - Static content should be at least 1024 tokens (minimum for caching)
    - Prompt structure should always place fixed instructions first
    - Dynamic/variable content should be at the end
    
    Args:
        static_instructions (str): Fixed instructions, system prompts, examples, etc.
        dynamic_content (str): Variable content like user input or specific data
        
    Returns:
        str: A properly structured prompt for optimal caching
    """
    return f"{static_instructions}\n\n{dynamic_content}"


def call_llm(
    prompt: str, 
    model: str = "gpt-4o", 
    temperature: float = 0.7, 
    max_tokens: Optional[int] = None, 
    content_length: Optional[int] = None,
    content_type: str = "default",
    timeout: int = 60
) -> str:
    """
    Calls an LLM API with the given prompt and returns the response.
    
    Args:
        prompt (str): The prompt to send to the LLM
        model (str): The model to use (default: gpt-4o)
        temperature (float): Controls randomness (0.0-1.0)
        max_tokens (int, optional): Maximum number of tokens to generate, if None will be calculated dynamically
        content_length (int, optional): Length of content for dynamic token scaling
        content_type (str): Type of content for scaling (default, topic, qa, transcript)
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        str: The LLM's response
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return "Error: OpenAI API key not found in environment variables."
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        
        try:
            # Start timing the API call
            start_time = time.time()
            logging.debug(f"Calling OpenAI API with prompt length {len(prompt)}")
            
            # If content_length wasn't provided, use the prompt length
            if content_length is None:
                content_length = len(prompt)
                
            # Dynamically calculate max_tokens if not provided
            if max_tokens is None:
                max_tokens = calculate_max_tokens(
                    content_length=content_length,
                    content_type=content_type
                )
                logging.debug(f"Dynamically calculated max_tokens: {max_tokens} for content_length {content_length} and type {content_type}")
            
            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI API call completed in {elapsed:.2f} seconds")
            
            # Track token usage for cost calculation
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cached_tokens = 0
            
            # Check if we have cached tokens information
            if hasattr(response.usage, 'prompt_tokens_details') and \
               hasattr(response.usage.prompt_tokens_details, 'cached_tokens'):
                cached_tokens = response.usage.prompt_tokens_details.cached_tokens
                logging.debug(f"Cached tokens: {cached_tokens}")
            
            # Add metrics to the global tracker
            global_metrics.add_api_call(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                model=model
            )
            
            logging.debug(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, Cached: {cached_tokens}")
            
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


def call_llm_cached(
    static_instructions: str, 
    dynamic_content: str, 
    model: str = "gpt-4o", 
    temperature: float = 0.7, 
    max_tokens: Optional[int] = None,
    content_length: Optional[int] = None,
    content_type: str = "default",
    timeout: int = 60
) -> str:
    """
    Calls an LLM API with a prompt structured for optimal caching.
    Places static instructions first and dynamic content last to maximize cache hits.
    
    Args:
        static_instructions (str): Fixed instructions, system prompts, examples, etc.
        dynamic_content (str): Variable content like user input or specific data
        model (str): The model to use (default: gpt-4o)
        temperature (float): Controls randomness (0.0-1.0)
        max_tokens (int, optional): Maximum number of tokens to generate, if None will be calculated dynamically
        content_length (int, optional): Length of content for dynamic token scaling
        content_type (str): Type of content for scaling (default, topic, qa, transcript)
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        str: The LLM's response
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return "Error: OpenAI API key not found in environment variables."
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        
        try:
            # Start timing the API call
            start_time = time.time()
            
            # Create system and user messages
            system_message = {"role": "system", "content": static_instructions}
            user_message = {"role": "user", "content": dynamic_content}
            messages = [system_message, user_message]
            
            logging.debug(f"Calling OpenAI API with cached prompt (system: {len(static_instructions)}, user: {len(dynamic_content)})")
            
            # If content_length wasn't provided, use dynamic content length
            if content_length is None:
                content_length = len(dynamic_content)
                
            # Dynamically calculate max_tokens if not provided
            if max_tokens is None:
                max_tokens = calculate_max_tokens(
                    content_length=content_length,
                    content_type=content_type
                )
                logging.debug(f"Dynamically calculated max_tokens: {max_tokens} for content_length {content_length} and type {content_type}")
            
            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI API call completed in {elapsed:.2f} seconds")
            
            # Track token usage for cost calculation
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cached_tokens = 0
            
            # Check if we have cached tokens information
            if hasattr(response.usage, 'prompt_tokens_details') and \
               hasattr(response.usage.prompt_tokens_details, 'cached_tokens'):
                cached_tokens = response.usage.prompt_tokens_details.cached_tokens
                logging.debug(f"Cached tokens: {cached_tokens}")
            
            # Add metrics to the global tracker
            global_metrics.add_api_call(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                model=model
            )
            
            logging.debug(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, Cached: {cached_tokens}")
            
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


def call_llm_with_structured_output(
    prompt: str, 
    response_format: Dict[str, Any], 
    model: str = "gpt-4o", 
    max_tokens: Optional[int] = None, 
    temperature: float = 0.7,
    content_length: Optional[int] = None,
    content_type: str = "default",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Calls an LLM API with structured output capabilities using the OpenAI Responses API.
    
    Args:
        prompt (str): The prompt to send to the LLM
        response_format (Dict[str, Any]): Format specification for the response
        model (str): The model to use (default: gpt-4o)
        max_tokens (int, optional): Maximum number of tokens to generate, if None will be calculated dynamically
        temperature (float): Controls randomness (0.0-1.0)
        content_length (int, optional): Length of content for dynamic token scaling
        content_type (str): Type of content for scaling (default, topic, qa, transcript)
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        Dict[str, Any]: Structured response from the API
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return {"error": "OpenAI API key not found in environment variables."}
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        
        try:
            # Start timing the API call
            start_time = time.time()
            logging.debug(f"Calling OpenAI Responses API with prompt length {len(prompt)}")
            
            # If content_length wasn't provided, use the prompt length
            if content_length is None:
                content_length = len(prompt)
                
            # Dynamically calculate max_tokens if not provided
            if max_tokens is None:
                max_tokens = calculate_max_tokens(
                    content_length=content_length,
                    content_type=content_type
                )
                logging.debug(f"Dynamically calculated max_tokens: {max_tokens} for content_length {content_length} and type {content_type}")
            
            # Make the API call
            response = client.responses.create(
                model=model,
                input=[{"role": "user", "content": prompt}],
                response_format=response_format,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI Responses API call completed in {elapsed:.2f} seconds")
            
            # Track token usage for cost calculation
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cached_tokens = 0
            
            # Check if we have cached tokens information
            if hasattr(response.usage, 'input_tokens_details') and \
               hasattr(response.usage.input_tokens_details, 'cached_tokens'):
                cached_tokens = response.usage.input_tokens_details.cached_tokens
                logging.debug(f"Cached tokens: {cached_tokens}")
            
            # Add metrics to the global tracker
            global_metrics.add_api_call(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                model=model
            )
            
            logging.debug(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, Cached: {cached_tokens}")
            
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


def call_llm_structured_output_cached(
    prompt: Union[str, Dict[str, str]], 
    response_format: Dict[str, Any], 
    model: str = "gpt-4o", 
    max_tokens: Optional[int] = None, 
    temperature: float = 0.7,
    content_length: Optional[int] = None,
    content_type: str = "default",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Calls an LLM API with structured output capabilities and support for cached prompts.
    
    Args:
        prompt (Union[str, Dict[str, str]]): Either a string prompt or a dictionary with 'instructions' and 'content' keys
        response_format (Dict[str, Any]): Format specification for the response
        model (str): The model to use (default: gpt-4o)
        max_tokens (int, optional): Maximum number of tokens to generate, if None will be calculated dynamically
        temperature (float): Controls randomness (0.0-1.0)
        content_length (int, optional): Length of content for dynamic token scaling
        content_type (str): Type of content for scaling (default, topic, qa, transcript)
        timeout (int): Maximum time to wait for a response in seconds
        
    Returns:
        Dict[str, Any]: Structured response from the API
    """
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        return {"error": "OpenAI API key not found in environment variables."}
    
    # Initialize the OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        
        try:
            # Start timing the API call
            start_time = time.time()
            
            # Process the prompt based on its type
            if isinstance(prompt, dict):
                # We have a cacheable prompt with separated components
                system_prompt = prompt.get("instructions", "")
                user_prompt = prompt.get("content", "")
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                logging.debug(f"Calling OpenAI Responses API with cacheable prompt (system: {len(system_prompt)}, user: {len(user_prompt)})")
                
                # Use the content length of the user prompt for scaling if not provided
                if content_length is None:
                    content_length = len(user_prompt)
            else:
                # We have a standard prompt string
                messages = [{"role": "user", "content": prompt}]
                logging.debug(f"Calling OpenAI Responses API with prompt length {len(prompt)}")
                
                # Use the content length of the prompt for scaling if not provided
                if content_length is None:
                    content_length = len(prompt)
            
            # Dynamically calculate max_tokens if not provided
            if max_tokens is None:
                max_tokens = calculate_max_tokens(
                    content_length=content_length,
                    content_type=content_type
                )
                logging.debug(f"Dynamically calculated max_tokens: {max_tokens} for content_length {content_length} and type {content_type}")
            
            # Make the API call with structured output
            response = client.responses.create(
                model=model,
                input=messages,
                response_format=response_format,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            # Calculate and log response time
            elapsed = time.time() - start_time
            logging.debug(f"OpenAI Responses API call completed in {elapsed:.2f} seconds")
            
            # Track token usage for cost calculation
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cached_tokens = 0
            
            # Check if we have cached tokens information
            if hasattr(response.usage, 'input_tokens_details') and \
               hasattr(response.usage.input_tokens_details, 'cached_tokens'):
                cached_tokens = response.usage.input_tokens_details.cached_tokens
                logging.debug(f"Cached tokens: {cached_tokens}")
            
            # Add metrics to the global tracker
            global_metrics.add_api_call(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                model=model
            )
            
            logging.debug(f"Tokens - Input: {input_tokens}, Output: {output_tokens}, Cached: {cached_tokens}")
            
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
    
    # Test the cache-optimized call_llm_cached function
    print("\n2. Testing cache-optimized call_llm_cached function...")
    static_instructions = """
    You are an expert at explaining technical concepts clearly and concisely.
    When explaining tools or software, focus on their primary purpose and benefits.
    Use simple language that anyone can understand.
    Avoid technical jargon whenever possible.
    Structure your response to be direct and to the point.
    Aim to provide value in as few words as needed.
    """
    dynamic_content = "Explain what a YouTube video summarizer does in one sentence."
    
    cached_response = call_llm_cached(static_instructions, dynamic_content, max_tokens=100)
    print(f"Static Instructions: {static_instructions[:50]}...")
    print(f"Dynamic Content: {dynamic_content}")
    print(f"Response: {cached_response}")
    
    # Test the structured output function
    print("\n3. Testing call_llm_with_structured_output function...")
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
        "required": ["explanation", "key_features"]
    }
    
    structured_response = call_llm_with_structured_output(
        prompt="Explain what a YouTube video summarizer does and list its key features.",
        response_format={"type": "json_object", "schema": schema},
        temperature=0.5
    )
    
    print("Schema:", json.dumps(schema, indent=2))
    print("Structured Response:", json.dumps(structured_response, indent=2))
    
    # Test dynamic token scaling
    print("\n4. Testing dynamic token scaling...")
    short_transcript = "This is a short transcript of about 500 characters."
    medium_transcript = "This is a medium transcript " + "with repeated content " * 30  # Around 5000 chars
    
    for transcript in [short_transcript, medium_transcript]:
        print(f"\nTesting with transcript of length {len(transcript)}")
        response = call_llm(
            prompt="Summarize this transcript: " + transcript,
            content_length=len(transcript),
            content_type="transcript"
        )
        print(f"Response length: {len(response)} characters")
