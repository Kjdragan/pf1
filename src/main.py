"""
YouTube Video Summarizer - Main Application
"""
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nodes.input_processing_node import InputProcessingNode
from src.nodes.content_extraction_node import ContentExtractionNode
from src.nodes.topic_extraction_node import TopicExtractionNode
from src.nodes.topic_orchestrator_node import TopicOrchestratorNode
from src.nodes.html_generation_node import HTMLGenerationNode
from src.utils.logger import logger

def run_pipeline(youtube_url, output_dir="output", enable_chunking=False, max_workers=3):
    """
    Run the complete YouTube video summarization pipeline.
    
    Args:
        youtube_url (str): URL of the YouTube video to summarize
        output_dir (str): Directory to save the output HTML file
        enable_chunking (bool): Whether to enable transcript chunking
        max_workers (int): Maximum number of parallel workers for topic processing
    """
    logger.info(f"{'='*60}")
    logger.info(f"YouTube Video Summarizer")
    logger.info(f"{'='*60}")
    logger.info(f"Processing URL: {youtube_url}")
    logger.info(f"Chunking: {'Enabled' if enable_chunking else 'Disabled'}")
    logger.info(f"Parallel Workers: {max_workers}")
    logger.info(f"{'='*60}")
    
    # Initialize shared memory
    shared_memory = {"video_url": youtube_url}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Output directory created/confirmed: {output_dir}")
    
    # Configure chunking parameters if enabled
    chunk_size = 4000 if enable_chunking else 0
    overlap = 500 if enable_chunking else 0
    
    try:
        # 1. Input Processing Node
        logger.info("[1/5] Starting Input Processing...")
        input_node = InputProcessingNode(shared_memory)
        shared_memory = input_node.run()
        
        # Check for errors
        if "error" in shared_memory:
            logger.error(f"Input Processing failed: {shared_memory['error']}")
            return shared_memory
        
        logger.info(f"Successfully processed video: {shared_memory.get('metadata', {}).get('title', 'Unknown')}")
        
        # 2. Content Extraction Node
        logger.info("[2/5] Starting Content Extraction...")
        content_node = ContentExtractionNode(shared_memory)
        shared_memory = content_node.run()
        
        # Check for errors
        if "error" in shared_memory:
            logger.error(f"Content Extraction failed: {shared_memory['error']}")
            return shared_memory
        
        transcript_length = len(shared_memory.get('transcript', ''))
        logger.info(f"Successfully extracted transcript ({transcript_length} characters)")
        
        # 3. Topic Extraction Node
        logger.info("[3/5] Starting Topic Extraction...")
        topic_node = TopicExtractionNode(shared_memory, chunk_size=chunk_size, overlap=overlap)
        shared_memory = topic_node.run()
        
        # Check for errors
        if "error" in shared_memory:
            logger.error(f"Topic Extraction failed: {shared_memory['error']}")
            return shared_memory
        
        topics = shared_memory.get('topics', [])
        logger.info(f"Successfully extracted {len(topics)} topics")
        for i, topic in enumerate(topics):
            logger.info(f"  Topic {i+1}: {topic}")
        
        # 4. Topic Processing Orchestrator Node
        logger.info("[4/5] Starting Topic Processing...")
        orchestrator_node = TopicOrchestratorNode(shared_memory, max_workers=max_workers, questions_per_topic=3)
        shared_memory = orchestrator_node.run()
        
        # Check for errors
        if "error" in shared_memory:
            logger.error(f"Topic Processing failed: {shared_memory['error']}")
            return shared_memory
        
        qa_pairs = shared_memory.get('qa_pairs', {})
        eli5_content = shared_memory.get('eli5_content', {})
        total_qa_pairs = sum(len(pairs) for pairs in qa_pairs.values())
        
        logger.info(f"Successfully processed {len(topics)} topics")
        logger.info(f"Generated {total_qa_pairs} Q&A pairs and {len(eli5_content)} ELI5 explanations")
        
        # 5. HTML Generation Node
        logger.info("[5/5] Starting HTML Generation...")
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = shared_memory.get("video_id", "unknown")
        output_file = os.path.join(output_dir, f"summary_{video_id}_{timestamp}.html")
        
        html_node = HTMLGenerationNode(shared_memory, output_file)
        shared_memory = html_node.run()
        
        # Check for errors
        if "error" in shared_memory:
            logger.error(f"HTML Generation failed: {shared_memory['error']}")
            return shared_memory
        
        # Print summary
        logger.info(f"{'='*60}")
        logger.info("Summary Generation Complete!")
        logger.info(f"{'='*60}")
        logger.info(f"Video: {shared_memory.get('metadata', {}).get('title', 'Unknown')}")
        logger.info(f"Topics: {len(shared_memory.get('topics', []))}")
        logger.info(f"Q&A Pairs: {sum(len(pairs) for pairs in shared_memory.get('qa_pairs', {}).values())}")
        logger.info(f"Output File: {output_file}")
        logger.info(f"{'='*60}")
        
        return shared_memory
        
    except Exception as e:
        logger.exception(f"Unexpected error in pipeline: {str(e)}")
        shared_memory["error"] = f"Pipeline error: {str(e)}"
        return shared_memory

def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(description="YouTube Video Summarizer")
    parser.add_argument("url", nargs='?', default=None, help="YouTube video URL to summarize")
    parser.add_argument("--output", "-o", default="output", help="Output directory for HTML summary")
    parser.add_argument("--chunk", action="store_true", help="Enable transcript chunking for long videos")
    parser.add_argument("--workers", "-w", type=int, default=3, help="Number of parallel workers for topic processing")
    
    args = parser.parse_args()
    
    # If no URL is provided as a command-line argument, ask for user input
    youtube_url = args.url
    if not youtube_url:
        youtube_url = input("Please enter a YouTube URL to summarize: ")
    
    logger.info(f"Starting YouTube Video Summarizer with URL: {youtube_url}")
    
    # Run the pipeline
    run_pipeline(youtube_url, args.output, args.chunk, args.workers)

if __name__ == "__main__":
    main()
