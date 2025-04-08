"""
Base node class for YouTube Video Summarizer.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from abc import ABC, abstractmethod
from src.utils.logger import logger

class BaseNode(ABC):
    """
    Abstract base class for all nodes in the YouTube Video Summarizer.
    """
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary for data exchange between nodes
        """
        self.shared_memory = shared_memory or {}
        self.node_name = self.__class__.__name__
        logger.debug(f"{self.node_name} initialized")
    
    @abstractmethod
    def prep(self):
        """
        Prepare for execution by reading necessary data from shared memory.
        """
        pass
    
    @abstractmethod
    def exec(self):
        """
        Execute the node's main functionality.
        """
        pass
    
    @abstractmethod
    def post(self):
        """
        Post-process and write results to shared memory.
        """
        pass
    
    def run(self):
        """
        Run the complete node workflow: prep, exec, post.
        
        Returns:
            dict: The updated shared memory
        """
        logger.debug(f"{self.node_name} starting run")
        try:
            self.prep()
            if "error" not in self.shared_memory:
                self.exec()
            if "error" not in self.shared_memory:
                self.post()
            
            if "error" in self.shared_memory:
                logger.error(f"{self.node_name} failed: {self.shared_memory['error']}")
            else:
                logger.debug(f"{self.node_name} completed successfully")
                
        except Exception as e:
            logger.exception(f"Unexpected error in {self.node_name}: {str(e)}")
            self.shared_memory["error"] = f"{self.node_name} error: {str(e)}"
            
        return self.shared_memory
