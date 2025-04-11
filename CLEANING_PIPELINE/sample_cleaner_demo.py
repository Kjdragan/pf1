"""
Sample demonstration of the Tavily Cleaner module.

This script demonstrates how to use the Tavily Cleaner module with the sample search results.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import from CLEANING_PIPELINE
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CLEANING_PIPELINE.tavily_cleaner.cleaner import clean_tavily_results


def main():
    """Run the sample demonstration."""
    # Path to the sample search results
    sample_path = Path(__file__).parent / "Sample_raw_search results" / "tavily_results_what_are_the_latest_news_from__20250411_152423.json"
    
    # Output path
    output_path = Path(__file__).parent / "cleaned_results.json"
    
    print(f"Loading sample search results from {sample_path}...")
    
    # Load the sample search results
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_results = json.load(f)
    
    print("Sample search results loaded.")
    print(f"Query: {sample_results.get('query')}")
    print(f"Number of results: {len(sample_results.get('results', []))}")
    
    # Clean the search results
    print("\nCleaning search results...")
    cleaned_results = clean_tavily_results(sample_results, output_format="dict")
    
    # Print some statistics
    result_count = len(cleaned_results.get('results', []))
    print(f"Processed {result_count} results.")
    
    # Calculate content reduction
    total_original = 0
    total_cleaned = 0
    
    for result in cleaned_results.get('results', []):
        meta = result.get('extraction_metadata', {})
        total_original += meta.get('original_length', 0)
        total_cleaned += meta.get('cleaned_length', 0)
    
    if total_original > 0:
        reduction_pct = (1 - (total_cleaned / total_original)) * 100
        print(f"Content reduction: {reduction_pct:.1f}% (from {total_original} to {total_cleaned} characters)")
    
    # Save the cleaned results
    print(f"\nSaving cleaned results to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_results, f, indent=2)
    
    print("Done!")
    
    # Print extraction strategies used
    print("\nExtraction strategies used:")
    strategies = {}
    for result in cleaned_results.get('results', []):
        meta = result.get('extraction_metadata', {})
        strategy = meta.get('strategy', 'unknown')
        strategies[strategy] = strategies.get(strategy, 0) + 1
    
    for strategy, count in strategies.items():
        print(f"  - {strategy}: {count} results")


if __name__ == "__main__":
    main()
