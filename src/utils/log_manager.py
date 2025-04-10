"""
Log directory management utility.
Provides functions to clear log directories and ensure they exist.
"""

import os
import shutil
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def ensure_dir_exists(directory: str) -> None:
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        directory (str): Path to the directory
    """
    os.makedirs(directory, exist_ok=True)
    logger.debug(f"Ensured directory exists: {directory}")

def clear_directory(directory: str, exclude: Optional[List[str]] = None) -> None:
    """
    Clears all files and subdirectories in the specified directory.
    
    Args:
        directory (str): Path to the directory to clear
        exclude (List[str], optional): List of filenames to exclude from clearing
    """
    if not os.path.exists(directory):
        logger.debug(f"Directory does not exist, creating: {directory}")
        os.makedirs(directory, exist_ok=True)
        return
        
    exclude = exclude or []
    
    # Get all items in the directory
    items = os.listdir(directory)
    
    for item in items:
        # Skip excluded items (either exact match or contains an excluded substring)
        skip = False
        for exclusion in exclude:
            if exclusion in item:
                skip = True
                logger.debug(f"Skipping {item} (matched exclusion pattern {exclusion})")
                break
                
        if skip:
            continue
            
        item_path = os.path.join(directory, item)
        
        try:
            if os.path.isfile(item_path):
                try:
                    os.unlink(item_path)
                    logger.debug(f"Cleared file: {item_path}")
                except PermissionError:
                    logger.debug(f"Skipping file that's in use: {item_path}")
            elif os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)
                    logger.debug(f"Cleared directory: {item_path}")
                except PermissionError:
                    logger.debug(f"Skipping directory that's in use: {item_path}")
        except Exception as e:
            logger.error(f"Error clearing {item_path}: {str(e)}")
            
    logger.info(f"Cleared directory: {directory}")

def clear_log_directories(base_dir: Optional[str] = None, preserve_current: bool = True) -> None:
    """
    Clears all log directories for a fresh run.
    
    Args:
        base_dir (str, optional): Base directory of the project
        preserve_current (bool): Whether to preserve the currently active log file
    """
    if base_dir is None:
        # Get the project root directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    # Define log directories to clear
    log_dirs = [
        os.path.join(base_dir, "logs"),
        os.path.join(base_dir, "logs", "prompts")
    ]
    
    # Ensure the directories exist
    for directory in log_dirs:
        ensure_dir_exists(directory)

    # Get the current date-time for identifying currently active log files
    current_date = os.path.basename(logging.getLoggerClass().root.handlers[0].baseFilename) if preserve_current and hasattr(logging.getLoggerClass().root, 'handlers') and logging.getLoggerClass().root.handlers else None

    # Define exclusions for the main logs directory
    main_exclusions = ["prompts"]
    
    # Add the current log file to exclusions if it's active
    if current_date and preserve_current:
        # We don't know the exact filename, but we know it contains today's date
        logger.debug(f"Will preserve current log file with date stamp: {current_date}")
        main_exclusions.append(current_date)
        
    # Clear the main logs directory with exclusions
    clear_directory(log_dirs[0], exclude=main_exclusions)
    
    # Clear the prompts directory
    clear_directory(log_dirs[1])
    
    logger.info("Log directories cleared for fresh run (preserving active files)")
