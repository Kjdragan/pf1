"""
HTML Generation Node for YouTube Video Summarizer.
"""
import sys
import os
from src.nodes.base_node import BaseNode
from src.utils.generate_html import generate_html
from src.utils.logger import logger

class HTMLGenerationNode(BaseNode):
    """
    Node for generating HTML visualization of the video summary.
    """
    
    def __init__(self, shared_memory=None, output_path=None):
        """
        Initialize the node with shared memory and output path.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            output_path (str): Path to save the HTML output file
        """
        super().__init__(shared_memory)
        self.output_path = output_path
        logger.debug(f"HTMLGenerationNode initialized with output_path={output_path}")
    
    def prep(self):
        """
        Prepare for execution by checking if all required data exists in shared memory.
        """
        required_keys = ["video_id", "metadata", "topics", "qa_pairs", "transformed_content"]
        missing_keys = [key for key in required_keys if key not in self.shared_memory]
        
        if missing_keys:
            error_msg = f"Missing required data in shared memory: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping HTML Generation due to previous error: {self.shared_memory['error']}")
            return
        
        logger.info("Preparing to generate HTML summary")
        logger.debug(f"Found {len(self.shared_memory['topics'])} topics and {len(self.shared_memory['transformed_content'])} transformed content blocks")
    
    def exec(self):
        """
        Execute HTML generation using the data in shared memory.
        """
        if "error" in self.shared_memory:
            return
            
        # Prepare the summary data for HTML generation
        summary_data = {
            "video_id": self.shared_memory["video_id"],
            "metadata": self.shared_memory["metadata"],
            "topics": self.shared_memory["topics"],
            "qa_pairs": self.shared_memory["qa_pairs"],
            "transformed_content": self.shared_memory["transformed_content"],
            "selected_rubric": self.shared_memory.get("selected_rubric", {}),
            "audience_level": self.shared_memory.get("audience_level", "sophisticated")
        }
        
        # Generate the HTML content
        logger.debug("Calling generate_html function")
        html_content = generate_html(summary_data)
        
        # Store the HTML content in shared memory
        self.shared_memory["html_output"] = html_content
        logger.info(f"Generated HTML content ({len(html_content)} characters)")
        
        # Save the HTML to a file if output_path is provided
        if self.output_path:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
                logger.debug(f"Ensuring output directory exists: {os.path.dirname(os.path.abspath(self.output_path))}")
                
                # Write the HTML content to the file
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                logger.info(f"HTML summary saved to: {self.output_path}")
            except Exception as e:
                error_msg = f"Failed to save HTML file: {str(e)}"
                logger.exception(error_msg)
                self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process after HTML generation.
        """
        if "error" in self.shared_memory:
            return
            
        if "html_output" in self.shared_memory and self.output_path:
            logger.info(f"HTML summary is available at: {os.path.abspath(self.output_path)}")
            logger.info("HTML Generation completed successfully")
        else:
            logger.warning("HTML summary was generated but may not have been saved to file")


if __name__ == "__main__":
    # Test with sample data
    test_data = {
        "video_id": "dQw4w9WgXcQ",
        "metadata": {
            "title": "Rick Astley - Never Gonna Give You Up",
            "channel_name": "Rick Astley",
            "duration": "3 minutes 33 seconds",
            "published_at": "October 25, 2009",
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
        },
        "topics": [
            "Music Video Plot",
            "Song Lyrics",
            "Cultural Impact"
        ],
        "qa_pairs": {
            "Music Video Plot": [
                {
                    "question": "What happens in the music video?",
                    "answer": "Rick dances and sings in different locations with backup dancers."
                },
                {
                    "question": "What is Rick wearing?",
                    "answer": "Rick is wearing a long coat and has styled hair."
                }
            ],
            "Song Lyrics": [
                {
                    "question": "What is the main message of the song?",
                    "answer": "The song is about commitment and never letting someone down."
                }
            ],
            "Cultural Impact": [
                {
                    "question": "Why is this song famous on the internet?",
                    "answer": "It became an internet prank called 'Rickrolling' where people are tricked into clicking links to this video."
                }
            ]
        },
        "transformed_content": {
            "Music Video Plot": "In this video, a man named Rick is dancing and singing. He moves his arms and legs in a funny way that people like to copy. He sings in different places like a stage and outside.",
            "Song Lyrics": "Rick is singing about being a good friend. He promises to always be there for someone special and never make them sad or tell lies. It's like when you promise to always be nice to your best friend.",
            "Cultural Impact": "This song became super famous because people on the internet started using it as a funny joke. They would trick their friends by saying 'click here for something cool' but the link would take them to this song instead. This joke is called 'Rickrolling'."
        }
    }
    
    # Initialize shared memory
    shared_memory = test_data
    
    # Create and run the node with a test output path
    test_output_path = "test_summary.html"
    node = HTMLGenerationNode(shared_memory, test_output_path)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    logger.info(f"HTML output length: {len(updated_memory.get('html_output', ''))}")
    logger.info(f"HTML file saved to: {test_output_path}")
