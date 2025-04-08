"""
Content Extraction Node for YouTube Video Summarizer.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.extract_youtube_transcript import extract_youtube_transcript
from src.utils.logger import logger

class ContentExtractionNode(BaseNode):
    """
    Node for extracting transcript from a YouTube video.
    """
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
        """
        super().__init__(shared_memory)
    
    def prep(self):
        """
        Prepare for execution by checking if video_id exists in shared memory.
        """
        if "video_id" not in self.shared_memory:
            error_msg = "YouTube video ID not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping Content Extraction due to previous error: {self.shared_memory['error']}")
            return
        
        logger.info(f"Extracting transcript for video ID: {self.shared_memory['video_id']}")
    
    def exec(self):
        """
        Execute transcript extraction.
        """
        if "error" in self.shared_memory:
            return
            
        # Extract the transcript
        video_id = self.shared_memory["video_id"]
        logger.debug(f"Calling YouTube transcript API for video ID: {video_id}")
        transcript = extract_youtube_transcript(video_id)
        
        # Check if there was an error
        if transcript.startswith("Error:"):
            logger.error(f"Transcript extraction failed: {transcript}")
            self.shared_memory["error"] = transcript
            return
        
        self.shared_memory["transcript"] = transcript
        
        # Log a preview of the transcript
        preview_length = min(150, len(transcript))
        logger.info(f"Extracted transcript ({len(transcript)} characters)")
        logger.debug(f"Transcript preview: {transcript[:preview_length]}...")
    
    def post(self):
        """
        Post-process and check for errors.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Content Extraction Node: {self.shared_memory['error']}")
            return
        
        if "transcript" not in self.shared_memory:
            error_msg = "Failed to extract transcript"
            logger.error(f"Error: {error_msg}")
            self.shared_memory["error"] = error_msg
            return
        
        logger.info("Content Extraction Node completed successfully")


if __name__ == "__main__":
    # Test the node with a sample video ID
    test_video_id = "dQw4w9WgXcQ"
    
    # Initialize shared memory
    shared_memory = {"video_id": test_video_id}
    
    # Create and run the node
    node = ContentExtractionNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    if "error" in updated_memory:
        logger.error(f"Error: {updated_memory['error']}")
    else:
        transcript = updated_memory.get("transcript", "")
        logger.info(f"Transcript length: {len(transcript)} characters")
        logger.info(f"Transcript preview: {transcript[:200]}...")
