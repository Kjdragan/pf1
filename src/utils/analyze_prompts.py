#!/usr/bin/env python
"""
Prompt Caching Analysis Tool - Analyzes collected prompts for OpenAI caching potential.

This script examines the consolidated prompt logs and provides insights on:
1. Common prefixes that could benefit from caching
2. Functions with high duplication rates
3. Recommendations for prompt restructuring
"""

import os
import sys
import json
import argparse
import datetime
from typing import Dict, Any, List, Tuple
import difflib

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.prompt_logger import analyze_all_prompts

# Minimum token threshold for OpenAI caching to be effective
OPENAI_CACHE_THRESHOLD = 1024

def estimate_tokens(text: str) -> int:
    """Estimate number of tokens in a text string"""
    # Simple estimation: 1 token is roughly 4 characters or 0.75 words
    return max(len(text) // 4, int(len(text.split()) * 0.75))

def find_common_prefix(prompts: List[str], min_length: int = 200) -> Tuple[str, int]:
    """Find the longest common prefix among all prompts"""
    if not prompts:
        return "", 0
    
    shortest = min(prompts, key=len)
    prefix_length = 0
    
    for i in range(min(min_length, len(shortest))):
        if all(p[i] == shortest[i] for p in prompts if len(p) > i):
            prefix_length += 1
        else:
            break
    
    if prefix_length < min_length:
        # For a deeper analysis, use difflib to find a more substantial common prefix
        for i in range(min_length, len(shortest)):
            # Use a tolerance to allow for small differences
            matches = sum(1 for p in prompts if p[:i].startswith(shortest[:i]) or difflib.SequenceMatcher(None, p[:i], shortest[:i]).ratio() > 0.9)
            if matches >= len(prompts) * 0.8:  # 80% match threshold
                prefix_length = i
            else:
                break
    
    return shortest[:prefix_length], prefix_length

def find_static_instructions(prompts: List[Dict[str, Any]], min_run_count: int = 2) -> List[Dict[str, Any]]:
    """
    Analyze prompts to identify potential static instructions that could benefit from caching.
    
    Args:
        prompts: List of prompt entries from the log
        min_run_count: Minimum number of different runs to consider
        
    Returns:
        List of identified static instruction candidates with metadata
    """
    # Group prompts by function first
    function_groups = {}
    for prompt in prompts:
        func = prompt.get("function", "unknown")
        if func not in function_groups:
            function_groups[func] = []
        function_groups[func].append(prompt)
    
    results = []
    
    for func, func_prompts in function_groups.items():
        # Only analyze functions with multiple prompts
        if len(func_prompts) < 2:
            continue
            
        # Check if prompts come from different runs
        run_ids = set(p.get("run_id", "") for p in func_prompts)
        if len(run_ids) < min_run_count:
            continue
        
        # Get the actual prompt texts
        prompt_texts = [p.get("prompt", "") for p in func_prompts]
        
        # Find the common prefix
        common_prefix, prefix_length = find_common_prefix(prompt_texts)
        estimated_tokens = estimate_tokens(common_prefix)
        
        # If the prefix is potentially cacheable
        if estimated_tokens > 0:
            results.append({
                "function": func,
                "call_count": len(func_prompts),
                "unique_runs": len(run_ids),
                "prefix_length": prefix_length,
                "prefix_tokens_estimate": estimated_tokens,
                "cacheable": estimated_tokens >= OPENAI_CACHE_THRESHOLD,
                "prefix_sample": common_prefix[:500] + "..." if len(common_prefix) > 500 else common_prefix,
                "savings_potential": len(func_prompts) - 1  # Each duplicate call could benefit
            })
    
    # Sort by potential savings (cacheable ones first)
    return sorted(results, key=lambda x: (not x["cacheable"], -x["savings_potential"]))

def analyze_prompt_duplication(prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze prompts for duplication within and across runs.
    
    Args:
        prompts: List of prompt entries from the log
        
    Returns:
        Dictionary with duplication analysis results
    """
    if not prompts:
        return {"error": "No prompts found"}
    
    # Count total and unique prompts
    total_prompts = len(prompts)
    unique_hashes = set(p.get("prompt_hash", "") for p in prompts)
    unique_count = len(unique_hashes)
    
    # Get duplicate rates by function
    function_stats = {}
    for prompt in prompts:
        func = prompt.get("function", "unknown")
        if func not in function_stats:
            function_stats[func] = {
                "count": 0,
                "hashes": set(),
                "runs": set(),
                "tokens_estimate": 0
            }
        
        function_stats[func]["count"] += 1
        function_stats[func]["hashes"].add(prompt.get("prompt_hash", ""))
        function_stats[func]["runs"].add(prompt.get("run_id", ""))
        function_stats[func]["tokens_estimate"] += prompt.get("prompt_tokens_estimate", 0)
    
    # Calculate duplicate rates and convert sets for JSON serialization
    for func in function_stats:
        function_stats[func]["unique_count"] = len(function_stats[func]["hashes"])
        function_stats[func]["run_count"] = len(function_stats[func]["runs"])
        function_stats[func]["duplicate_rate"] = (
            (function_stats[func]["count"] - function_stats[func]["unique_count"]) / 
            function_stats[func]["count"] if function_stats[func]["count"] > 0 else 0
        )
        function_stats[func]["hashes"] = list(function_stats[func]["hashes"])
        function_stats[func]["runs"] = list(function_stats[func]["runs"])
    
    # Sort functions by duplicate rate (highest first)
    sorted_functions = sorted(
        function_stats.items(), 
        key=lambda x: (x[1]["duplicate_rate"], x[1]["count"]), 
        reverse=True
    )
    
    return {
        "total_prompts": total_prompts,
        "unique_prompts": unique_count,
        "duplicate_rate": (total_prompts - unique_count) / total_prompts if total_prompts > 0 else 0,
        "functions": {k: v for k, v in sorted_functions}
    }

def load_prompts(file_path: str = None) -> List[Dict[str, Any]]:
    """
    Load prompts from the consolidated log file or a specified file.
    
    Args:
        file_path: Optional path to a specific log file
        
    Returns:
        List of prompt entries
    """
    if file_path is None:
        # Use the default consolidated log file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_dir, "logs", "prompts", "all_prompts.json")
    
    if not os.path.exists(file_path):
        print(f"Error: Prompt log file not found at {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            return prompts if isinstance(prompts, list) else []
    except Exception as e:
        print(f"Error loading prompts: {str(e)}")
        return []

def print_caching_analysis(prompts: List[Dict[str, Any]]) -> None:
    """
    Print an analysis of prompt caching potential to the console.
    
    Args:
        prompts: List of prompt entries from the log
    """
    if not prompts:
        print("No prompts found for analysis.")
        return
    
    # Get basic stats
    duplication = analyze_prompt_duplication(prompts)
    static_instructions = find_static_instructions(prompts)
    
    # Print header
    print("\n" + "="*80)
    print(f"PROMPT CACHING ANALYSIS REPORT - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Overall stats
    print(f"\n📊 OVERALL STATS:")
    print(f"  Total Prompts: {duplication['total_prompts']}")
    print(f"  Unique Prompts: {duplication['unique_prompts']}")
    print(f"  Duplicate Rate: {duplication['duplicate_rate']:.1%}")
    
    # Highlight functions with high duplication
    print(f"\n🔄 FUNCTIONS WITH HIGHEST DUPLICATION:")
    for i, (func, stats) in enumerate(duplication["functions"].items()):
        if i >= 5:  # Show top 5
            break
        print(f"  {func}:")
        print(f"    - Called {stats['count']} times across {stats['run_count']} runs")
        print(f"    - Duplicate rate: {stats['duplicate_rate']:.1%}")
        print(f"    - Estimated tokens: {stats['tokens_estimate']:.0f}")
    
    # Caching potential
    print(f"\n💾 CACHING POTENTIAL ANALYSIS:")
    print(f"  OpenAI caching requires at least {OPENAI_CACHE_THRESHOLD} tokens of identical prefix")
    
    cacheable_found = False
    for instr in static_instructions:
        cacheable = instr["cacheable"]
        prefix_tokens = instr["prefix_tokens_estimate"]
        
        if cacheable:
            cacheable_found = True
            print(f"\n  ✅ CACHEABLE: {instr['function']}")
            print(f"    - Found {prefix_tokens} token static prefix ({prefix_tokens - OPENAI_CACHE_THRESHOLD} above threshold)")
            print(f"    - Called {instr['call_count']} times in {instr['unique_runs']} runs")
            print(f"    - Potential savings: {instr['savings_potential']} calls could benefit from caching")
            print(f"    - Prefix sample: \"{instr['prefix_sample'][:100]}...\"")
    
    if not cacheable_found:
        print("\n  ❌ No cacheable static instructions found")
        
        # Show near misses
        near_misses = [i for i in static_instructions if not i["cacheable"] and i["prefix_tokens_estimate"] > OPENAI_CACHE_THRESHOLD * 0.5]
        if near_misses:
            print("\n  ⚠️ NEAR MISSES (could be restructured for caching):")
            for miss in near_misses[:3]:  # Show top 3 near misses
                tokens_needed = OPENAI_CACHE_THRESHOLD - miss["prefix_tokens_estimate"]
                print(f"    - {miss['function']}: Has {miss['prefix_tokens_estimate']} token prefix (needs {tokens_needed} more)")
    
    # Recommendations
    print("\n🔍 RECOMMENDATIONS:")
    if cacheable_found:
        print("  ✓ Some prompts already have cacheable static prefixes!")
        print("  ✓ Monitor your OpenAI usage to confirm caching is working")
    else:
        print("  ✗ No cacheable static prefixes found")
        print("  → Consider restructuring prompts to have longer static instructions")
        print(f"  → Static instructions should be at least {OPENAI_CACHE_THRESHOLD} tokens (~{OPENAI_CACHE_THRESHOLD * 4} characters)")
        print("  → Move dynamic content to the end of prompts")
        print("  → Use a templating approach with consistent static instructions")
    
    # Detailed analysis file option
    print("\n📋 DETAILED ANALYSIS:")
    print("  To save a detailed JSON analysis, use the --output option")
    
    print("\n" + "="*80)

def save_detailed_analysis(prompts: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save a detailed analysis to a JSON file.
    
    Args:
        prompts: List of prompt entries from the log
        output_file: Path to save the analysis
    """
    duplication = analyze_prompt_duplication(prompts)
    static_instructions = find_static_instructions(prompts)
    
    analysis = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_prompts": len(prompts),
        "duplication_analysis": duplication,
        "static_instruction_candidates": static_instructions,
        "caching_threshold": OPENAI_CACHE_THRESHOLD,
        "cacheable_candidates": [i for i in static_instructions if i["cacheable"]],
        "near_miss_candidates": [
            i for i in static_instructions 
            if not i["cacheable"] and i["prefix_tokens_estimate"] > OPENAI_CACHE_THRESHOLD * 0.5
        ]
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"Detailed analysis saved to: {output_file}")
    except Exception as e:
        print(f"Error saving analysis: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Analyze prompt logs for OpenAI caching potential")
    parser.add_argument("--input", "-i", help="Path to prompt log file (default: consolidated log)")
    parser.add_argument("--output", "-o", help="Path to save detailed analysis JSON")
    args = parser.parse_args()
    
    # Load prompts
    prompts = load_prompts(args.input)
    
    if not prompts:
        print("No prompts found. Run the application first to generate prompt logs.")
        return
    
    # Print analysis to console
    print_caching_analysis(prompts)
    
    # Save detailed analysis if requested
    if args.output:
        save_detailed_analysis(prompts, args.output)

if __name__ == "__main__":
    main()
