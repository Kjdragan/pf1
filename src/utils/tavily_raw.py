"""
Simple script to get raw Tavily search results.
This shows exactly what the Tavily SDK returns without any processing,
so we can understand the schema and decide on the best way to process it.
"""

from tavily import TavilyClient
import os
import json
import re
import datetime
from dotenv import load_dotenv
import argparse
from typing import Dict, Any, List
from pathlib import Path

# Load environment variables
load_dotenv()

def get_raw_tavily_results(query, max_results=5, include_raw=True):
    """
    Get raw Tavily search results without any processing.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        include_raw: Whether to include raw content
        
    Returns:
        The raw response from Tavily API
    """
    # Initialize Tavily client
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    if not tavily_api_key:
        return {"error": "TAVILY_API_KEY not found in environment variables"}
    
    tavily_client = TavilyClient(api_key=tavily_api_key)
    
    # Make the search request with minimal options
    try:
        # Search with specified options
        search_response = tavily_client.search(
            query=query,
            search_depth="advanced",
            include_raw_content=include_raw,
            include_answer=True,
            max_results=max_results
        )
        
        # Try to get a quick answer if available
        try:
            answer = tavily_client.qna_search(query=query)
            search_response["qna_answer"] = answer
        except Exception as e:
            search_response["qna_error"] = str(e)
        
        return search_response
    except Exception as e:
        return {"error": str(e)}

def estimate_tokens(text: str) -> int:
    """Roughly estimate the number of tokens in a text string.
    This is a simple approximation based on splitting by spaces and punctuation.
    """
    if not text:
        return 0
    # Split on spaces and punctuation
    tokens = re.findall(r'\w+|[^\w\s]', text)
    return len(tokens)


def truncate_if_needed(content: str, max_tokens: int = 15000) -> Dict[str, Any]:
    """Truncate content if it exceeds max_tokens, returning the content and metadata."""
    if not content:
        return {"content": "", "truncated": False, "original_length": 0, "estimated_tokens": 0}
    
    estimated_tokens = estimate_tokens(content)
    original_length = len(content)
    
    if estimated_tokens <= max_tokens:
        return {
            "content": content,
            "truncated": False,
            "original_length": original_length,
            "estimated_tokens": estimated_tokens
        }
    else:
        # Truncate proportionally to the token limit (approximate)
        char_ratio = max_tokens / estimated_tokens
        truncated_length = int(original_length * char_ratio) - 100  # Margin of safety
        truncated_content = content[:truncated_length] + f"... [TRUNCATED - {original_length-truncated_length} more characters]"
        
        return {
            "content": truncated_content,
            "truncated": True,
            "original_length": original_length,
            "estimated_tokens": estimated_tokens,
            "truncated_length": truncated_length
        }


def process_raw_results(results: Dict[str, Any], max_tokens_per_field: int = 15000) -> Dict[str, Any]:
    """Process raw results to truncate large fields while preserving JSON structure.
    
    Args:
        results: The raw results dictionary from Tavily
        max_tokens_per_field: Maximum tokens allowed per content field
        
    Returns:
        Processed results with any large fields safely truncated
    """
    processed_results = results.copy()
    
    # Extract schema information
    schema = {
        "top_level_keys": list(processed_results.keys()),
        "result_keys": []
    }
    
    if "results" in processed_results and isinstance(processed_results["results"], list):
        # Get schema of first result item if available
        if processed_results["results"] and isinstance(processed_results["results"][0], dict):
            schema["result_keys"] = list(processed_results["results"][0].keys())
        
        # Process each result item
        processed_items = []
        for i, result in enumerate(processed_results["results"]):
            processed_item = {}
            
            # Track which fields were truncated
            truncated_fields = []
            
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 1000:  # Only process large text fields
                    truncation_info = truncate_if_needed(value, max_tokens_per_field)
                    processed_item[key] = truncation_info["content"]
                    
                    if truncation_info["truncated"]:
                        truncated_fields.append({
                            "field": key,
                            "original_length": truncation_info["original_length"],
                            "estimated_tokens": truncation_info["estimated_tokens"]
                        })
                        # Add truncation metadata
                        processed_item[f"{key}_meta"] = {
                            "truncated": True,
                            "original_length": truncation_info["original_length"],
                            "estimated_tokens": truncation_info["estimated_tokens"]
                        }
                else:
                    # Keep as is
                    processed_item[key] = value
            
            # Add result number for easier reference
            processed_item["result_num"] = i + 1
            processed_items.append(processed_item)
            
            # Print truncation info
            if truncated_fields:
                print(f"Result {i+1}: Truncated {len(truncated_fields)} fields:")
                for tf in truncated_fields:
                    print(f"  - {tf['field']}: {tf['original_length']} chars, ~{tf['estimated_tokens']} tokens")
            else:
                print(f"Result {i+1}: No fields truncated")
        
        processed_results["results"] = processed_items
    
    # Add schema information
    processed_results["_schema_info"] = schema
    return processed_results
    

def ensure_docs_dir():
    """Ensure the docs directory exists."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        docs_dir.mkdir()
    return docs_dir


def get_output_filename(query: str):
    """Generate a filename for the output file based on query and timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean the query to create a valid filename
    clean_query = re.sub(r'[^\w\s]', '', query).replace(' ', '_').lower()[:30]
    return f"tavily_results_{clean_query}_{timestamp}.json"


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Get raw Tavily search results')
    parser.add_argument('query', type=str, help='Search query')
    parser.add_argument('--max-results', type=int, default=5, help='Max number of search results')
    parser.add_argument('--no-raw', action='store_true', help='Do not include raw content in results')
    parser.add_argument('--token-limit', type=int, default=15000, 
                        help='Max tokens per content field (approximate)')
    parser.add_argument('--schema-only', action='store_true', 
                        help='Only show schema information without content')
    parser.add_argument('--output-file', type=str, help='Custom output filename')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
    
    args = parser.parse_args()
    
    # Get raw results
    print(f"Fetching Tavily results for query: '{args.query}'\n")
    raw_results = get_raw_tavily_results(
        args.query, 
        max_results=args.max_results,
        include_raw=not args.no_raw
    )
    
    # Basic statistics before processing
    result_count = len(raw_results.get('results', []))
    raw_content_count = sum(1 for r in raw_results.get('results', []) if 'raw_content' in r)
    content_count = sum(1 for r in raw_results.get('results', []) if 'content' in r)
    
    print(f"\nRAW RESULTS STATISTICS:")
    print(f"Total results: {result_count}")
    print(f"Results with raw_content: {raw_content_count}")
    print(f"Results with content: {content_count}")
    
    # Top-level keys in response
    print(f"\nTOP-LEVEL KEYS IN RESPONSE:")
    for key in raw_results.keys():
        print(f"- {key}")
    
    # Keys in a result item if available
    if raw_results.get('results') and raw_results['results']:
        first_result = raw_results['results'][0]
        print(f"\nKEYS IN RESULT ITEM:")
        for key in first_result.keys():
            value_type = type(first_result[key]).__name__
            value_length = len(first_result[key]) if isinstance(first_result[key], str) else 'N/A'
            print(f"- {key}: {value_type}" + 
                  (f", length: {value_length} chars" if isinstance(first_result[key], str) else ""))
    
    # If schema-only mode, we're done
    if args.schema_only:
        print("\nSchema-only mode enabled. Exiting without processing content.")
        exit(0)
    
    # Process the results to truncate large fields
    processed_results = process_raw_results(raw_results, args.token_limit)
    
    # Print the processed results (summary only to avoid terminal overflow)
    print(f"\nPROCESSED TAVILY RESULTS: (full results will be saved to file)")
    
    # Create a summary version for terminal display
    display_results = processed_results.copy()
    if 'results' in display_results:
        for result in display_results['results']:
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 500:
                    result[key] = value[:500] + "... [truncated for display]"
    
    # Print the summarized version
    print(json.dumps(display_results, indent=2))
    
    # Save to file
    if not args.no_save:
        docs_dir = ensure_docs_dir()
        output_filename = args.output_file if args.output_file else get_output_filename(args.query)
        output_path = docs_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nFull results saved to: {output_path}")
    
    # Example raw content preview
    if raw_content_count > 0:
        first_raw = next((r for r in raw_results.get('results', []) if 'raw_content' in r), None)
        if first_raw:
            raw_sample = first_raw.get('raw_content', '')[:500]
            print(f"\nEXAMPLE RAW CONTENT (first 500 chars):\n{raw_sample}...")
    
    # Example content preview
    if content_count > 0:
        first_content = next((r for r in raw_results.get('results', []) if 'content' in r), None)
        if first_content:
            content_sample = first_content.get('content', '')[:500]
            print(f"\nEXAMPLE CONTENT (first 500 chars):\n{content_sample}...")
