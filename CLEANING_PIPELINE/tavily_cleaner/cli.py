"""
Command-line interface for Tavily Results Cleaner.

This module provides a command-line interface for cleaning Tavily search results.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .cleaner import clean_tavily_results


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        The loaded JSON data as a dictionary
        
    Raises:
        ValueError: If the file cannot be loaded or parsed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading file {file_path}: {e}")


def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Save JSON data to a file.
    
    Args:
        data: The data to save
        file_path: Path to the output file
        
    Raises:
        ValueError: If the data cannot be saved
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"Error saving to file {file_path}: {e}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Clean Tavily search results to extract the most relevant content.'
    )
    
    # Input options
    parser.add_argument(
        'input',
        help='Path to the input JSON file containing Tavily search results'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        help='Path to the output JSON file (default: input_file_cleaned.json)'
    )
    
    # Processing options
    parser.add_argument(
        '--max-chars',
        type=int,
        default=10000,
        help='Maximum number of characters to keep per result (default: 10000)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=5000,
        help='Maximum number of tokens to keep per result (default: 5000)'
    )
    
    parser.add_argument(
        '--keep-raw',
        action='store_true',
        help='Keep raw content in the output (default: False)'
    )
    
    # Output format options
    parser.add_argument(
        '--format',
        choices=['json', 'dict'],
        default='dict',
        help='Output format (default: dict)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    try:
        # Load input data
        print(f"Loading Tavily results from {args.input}...")
        input_data = load_json_file(args.input)
        
        # Process the data
        print("Cleaning Tavily results...")
        cleaned_data = clean_tavily_results(
            input_data,
            output_format=args.format
        )
        
        # Save the output
        print(f"Saving cleaned results to {args.output}...")
        save_json_file(cleaned_data, args.output)
        
        print("Done!")
        
        # Print some statistics
        if isinstance(cleaned_data, dict):
            result_count = len(cleaned_data.get('results', []))
            print(f"Processed {result_count} results.")
            
            # Calculate content reduction
            total_original = 0
            total_cleaned = 0
            
            for result in cleaned_data.get('results', []):
                meta = result.get('extraction_metadata', {})
                total_original += meta.get('original_length', 0)
                total_cleaned += meta.get('cleaned_length', 0)
            
            if total_original > 0:
                reduction_pct = (1 - (total_cleaned / total_original)) * 100
                print(f"Content reduction: {reduction_pct:.1f}% (from {total_original} to {total_cleaned} characters)")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
