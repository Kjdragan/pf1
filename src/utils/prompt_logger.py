"""
Utility for logging prompts sent to LLM APIs to enable analysis of caching potential.
Saves all prompts to JSON files for later analysis of overlapping content.
"""

import os
import json
import time
import datetime
import hashlib
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class PromptLogger:
    def __init__(self, log_dir: str = None):
        """
        Initialize the prompt logger.
        
        Args:
            log_dir (str, optional): Directory to save prompt logs. Defaults to logs/prompts.
        """
        # Use default logs/prompts directory if not specified
        if log_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.log_dir = os.path.join(base_dir, "logs", "prompts")
        else:
            self.log_dir = log_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize the current log file
        self.current_log_file = None
        self.current_log_data = []
        
        # Initialize the consolidated log file (for easier analysis)
        self.consolidated_log_file = os.path.join(self.log_dir, "all_prompts.json")
        
        # Load existing consolidated data if it exists
        self.consolidated_data = []
        if os.path.exists(self.consolidated_log_file):
            try:
                with open(self.consolidated_log_file, 'r', encoding='utf-8') as f:
                    self.consolidated_data = json.load(f)
                logger.debug(f"Loaded {len(self.consolidated_data)} existing prompt logs from consolidated file")
            except Exception as e:
                logger.error(f"Error loading consolidated log file: {str(e)}")
                # Start with empty data if file is corrupted
                self.consolidated_data = []
        
        logger.debug(f"PromptLogger initialized with log directory: {self.log_dir}")
        
    def _compute_similarity_hash(self, text: str) -> str:
        """
        Compute a hash of the text for similarity comparison.
        
        Args:
            text (str): Text to hash
            
        Returns:
            str: Hash string for similarity comparison
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
        
    def log_prompt(self, 
                  prompt: str, 
                  model: str,
                  function_name: str, 
                  metadata: Dict[str, Any] = None) -> None:
        """
        Log a prompt to the current log file.
        
        Args:
            prompt (str): The prompt sent to the LLM
            model (str): The model used
            function_name (str): Name of the function making the LLM call
            metadata (Dict[str, Any], optional): Additional metadata about the prompt
        """
        timestamp = datetime.datetime.now().isoformat()
        run_id = os.path.basename(self.current_log_file).replace('prompts_', '').replace('.json', '') if self.current_log_file else datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create an entry for the log
        entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "function": function_name,
            "model": model,
            "prompt_length": len(prompt),
            "prompt_tokens_estimate": len(prompt.split()) * 1.3,  # Rough token estimate
            "prompt_hash": self._compute_similarity_hash(prompt),
            "prompt": prompt
        }
        
        # Add any additional metadata
        if metadata:
            entry.update(metadata)
            
        # Add to current log data
        self.current_log_data.append(entry)
        
        # Also add to consolidated data
        self.consolidated_data.append(entry)
        
        # Generate log file name if not already set
        if self.current_log_file is None:
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_log_file = os.path.join(self.log_dir, f"prompts_{date_str}.json")
            
        # Write to file immediately (for crash recovery)
        try:
            # Write current run file
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_log_data, f, indent=2, ensure_ascii=False)
                
            # Write consolidated file
            with open(self.consolidated_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.consolidated_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Logged prompt from {function_name} to {self.current_log_file} and consolidated file")
        except Exception as e:
            logger.error(f"Error logging prompt to file: {str(e)}")
            
    def start_new_log_file(self) -> None:
        """
        Start a new log file for the next run.
        """
        # Generate a new log file name
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.log_dir, f"prompts_{date_str}.json")
        self.current_log_data = []
        logger.debug(f"Started new prompt log file: {self.current_log_file}")
        
    def analyze_prompt_overlap(self, use_consolidated: bool = False) -> Dict[str, Any]:
        """
        Analyze the log data for prompt overlap potential.
        
        Args:
            use_consolidated (bool): Whether to analyze the consolidated data instead of just current run
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        data_to_analyze = self.consolidated_data if use_consolidated else self.current_log_data
        
        if not data_to_analyze:
            return {"error": "No prompts logged"}
        
        # Basic stats
        total_prompts = len(data_to_analyze)
        total_tokens = sum(entry.get("prompt_tokens_estimate", 0) for entry in data_to_analyze)
        unique_hashes = len(set(entry.get("prompt_hash", "") for entry in data_to_analyze))
        
        # Group by function for more detailed analysis
        function_stats = {}
        for entry in data_to_analyze:
            func = entry.get("function", "unknown")
            if func not in function_stats:
                function_stats[func] = {
                    "count": 0,
                    "unique_hashes": set(),
                    "total_tokens": 0
                }
            function_stats[func]["count"] += 1
            function_stats[func]["unique_hashes"].add(entry.get("prompt_hash", ""))
            function_stats[func]["total_tokens"] += entry.get("prompt_tokens_estimate", 0)
        
        # Convert for JSON serialization
        for func in function_stats:
            function_stats[func]["unique_count"] = len(function_stats[func]["unique_hashes"])
            function_stats[func]["duplicate_rate"] = (function_stats[func]["count"] - function_stats[func]["unique_count"]) / function_stats[func]["count"] if function_stats[func]["count"] > 0 else 0
            del function_stats[func]["unique_hashes"]
        
        # Find most common static prefixes across prompts
        common_prefix_length = 0
        if len(data_to_analyze) > 1:
            prompts = [entry.get("prompt", "") for entry in data_to_analyze]
            # Find the longest common prefix among all prompts
            shortest_prompt = min(prompts, key=len)
            for i in range(len(shortest_prompt)):
                if all(p[i] == shortest_prompt[i] for p in prompts):
                    common_prefix_length += 1
                else:
                    break
        
        return {
            "total_prompts": total_prompts,
            "estimated_total_tokens": total_tokens,
            "unique_prompts": unique_hashes,
            "potential_duplicate_rate": (total_prompts - unique_hashes) / total_prompts if total_prompts > 0 else 0,
            "common_prefix_length": common_prefix_length,
            "function_stats": function_stats,
            "data_source": "consolidated" if use_consolidated else "current_run"
        }

# Create a singleton instance
prompt_logger = PromptLogger()

# Simple function to log prompts for easy imports
def log_prompt(prompt: str, model: str, function_name: str, metadata: Dict[str, Any] = None) -> None:
    """
    Log a prompt using the singleton logger instance.
    
    Args:
        prompt (str): The prompt sent to the LLM
        model (str): The model used
        function_name (str): Name of the function making the LLM call
        metadata (Dict[str, Any], optional): Additional metadata about the prompt
    """
    prompt_logger.log_prompt(prompt, model, function_name, metadata)

# Function to start a new log file
def start_new_log_file() -> None:
    """
    Start a new prompt log file.
    """
    prompt_logger.start_new_log_file()

def analyze_all_prompts() -> Dict[str, Any]:
    """
    Analyze all prompts in the consolidated log file.
    
    Returns:
        Dict[str, Any]: Analysis results
    """
    return prompt_logger.analyze_prompt_overlap(use_consolidated=True)

# Testing function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Test the prompt logger
    logger = PromptLogger()
    
    # Log some test prompts
    logger.log_prompt(
        prompt="Tell me about the history of AI", 
        model="gpt-4o",
        function_name="test_function",
        metadata={"test": True}
    )
    
    logger.log_prompt(
        prompt="What is machine learning?", 
        model="gpt-4o",
        function_name="test_function",
        metadata={"test": True}
    )
    
    # Print the analysis
    analysis = logger.analyze_prompt_overlap()
    print(json.dumps(analysis, indent=2))
