"""
Input Processing Node for YouTube Video Summarizer.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.validate_youtube_url import validate_youtube_url
from src.utils.extract_youtube_metadata import extract_youtube_metadata
from src.utils.logger import logger

class InputProcessingNode(BaseNode):
    """
    Node for validating YouTube URL and extracting video metadata.
    """
    
    def __init__(self, shared_memory=None, youtube_url=None):
        """
        Initialize the node with shared memory and YouTube URL.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            youtube_url (str): YouTube URL to process
        """
        super().__init__(shared_memory)
        if youtube_url:
            self.shared_memory["video_url"] = youtube_url
    
    def prep(self):
        """
        Prepare for execution by checking if video_url exists in shared memory.
        """
        if "video_url" not in self.shared_memory:
            error_msg = "YouTube URL not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Processing YouTube URL: {self.shared_memory['video_url']}")
    
    def exec(self):
        """
        Execute URL validation and metadata extraction.
        """
        # Validate the YouTube URL
        youtube_url = self.shared_memory["video_url"]
        is_valid, video_id = validate_youtube_url(youtube_url)
        
        if not is_valid:
            error_msg = f"Invalid YouTube URL: {youtube_url}"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        self.shared_memory["video_id"] = video_id
        logger.info(f"Valid YouTube video ID: {video_id}")
        
        # Extract video metadata
        logger.debug(f"Extracting metadata for video ID: {video_id}")
        metadata = extract_youtube_metadata(video_id)
        
        if "error" in metadata:
            error_msg = f"Error extracting metadata: {metadata['error']}"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        self.shared_memory["metadata"] = metadata
        logger.info(f"Extracted metadata for video: {metadata.get('title', 'Unknown Title')}")
        logger.debug(f"Video metadata: {metadata}")
    
    def post(self):
        """
        Post-process and check for errors.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Input Processing Node: {self.shared_memory['error']}")
            return
        
        logger.info("Input Processing Node completed successfully")


if __name__ == "__main__":
    # Test the node with a sample YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Initialize shared memory
    shared_memory = {"video_url": test_url}
    
    # Create and run the node
    node = InputProcessingNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    logger.info(f"Video ID: {updated_memory.get('video_id', 'Not found')}")
    logger.info(f"Video Title: {updated_memory.get('metadata', {}).get('title', 'Not found')}")
    logger.info(f"Channel: {updated_memory.get('metadata', {}).get('channel_name', 'Not found')}")
    logger.info(f"Duration: {updated_memory.get('metadata', {}).get('duration', 'Not found')}")
