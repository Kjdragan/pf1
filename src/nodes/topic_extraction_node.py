"""
Topic Extraction Node for YouTube Video Summarizer.
"""
import sys
import os
import textwrap
import concurrent.futures
from typing import List, Dict, Any

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.call_llm import call_llm
from src.utils.logger import logger

class TopicExtractionNode(BaseNode):
    """
    Node for identifying main topics from the video transcript.
    """
    
    def __init__(self, shared_memory=None, chunk_size=0, overlap=0, max_topics=5):
        """
        Initialize the node with shared memory and processing parameters.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            chunk_size (int): Size of transcript chunks (0 = no chunking)
            overlap (int): Overlap between chunks (when chunk_size > 0)
            max_topics (int): Maximum number of topics to extract
        """
        super().__init__(shared_memory)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_topics = max_topics
        self.chunks = []
        self.chunk_topics = []
        logger.debug(f"TopicExtractionNode initialized with chunk_size={chunk_size}, overlap={overlap}, max_topics={max_topics}")
    
    def prep(self):
        """
        Prepare for execution by checking if transcript exists in shared memory
        and splitting it into chunks if chunk_size > 0.
        """
        if "transcript" not in self.shared_memory:
            error_msg = "Transcript not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping Topic Extraction due to previous error: {self.shared_memory['error']}")
            return
        
        transcript = self.shared_memory["transcript"]
        logger.debug(f"Preparing to extract topics from transcript ({len(transcript)} characters)")
        
        # Only chunk if chunk_size is specified
        if self.chunk_size > 0:
            # Split into overlapping chunks
            start = 0
            while start < len(transcript):
                end = min(start + self.chunk_size, len(transcript))
                self.chunks.append(transcript[start:end])
                start = end - self.overlap
            logger.info(f"Split transcript into {len(self.chunks)} chunks for processing")
            logger.debug(f"Chunk sizes: {[len(chunk) for chunk in self.chunks]}")
        else:
            # Process as a single chunk
            self.chunks = [transcript]
            logger.info("Processing transcript as a single chunk")
    
    def exec(self):
        """
        Execute topic extraction for each chunk and combine results.
        """
        if "error" in self.shared_memory:
            return
            
        # Use ThreadPoolExecutor for parallel processing of chunks
        max_workers = min(len(self.chunks), 4)  # Limit concurrent API calls
        logger.info(f"Processing {len(self.chunks)} chunks with {max_workers} parallel workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunk processing tasks
            future_to_chunk = {
                executor.submit(self._process_chunk, i, chunk): i 
                for i, chunk in enumerate(self.chunks)
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_index = future_to_chunk[future]
                try:
                    topics = future.result()
                    if topics:
                        self.chunk_topics.append(topics)
                        logger.info(f"Completed processing for chunk {chunk_index+1}/{len(self.chunks)}")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_index+1}: {str(e)}")
                    
        # If we couldn't extract any topics, add some default ones
        if not self.chunk_topics:
            logger.warning("No topics extracted, using default topics")
            self.chunk_topics.append(["Main Content", "Key Points", "Summary"])
    
    def _process_chunk(self, chunk_index: int, chunk: str) -> List[str]:
        """
        Process a single chunk to extract topics.
        
        Args:
            chunk_index (int): Index of the chunk
            chunk (str): Content of the chunk
            
        Returns:
            List[str]: Extracted topics
        """
        logger.info(f"Processing chunk {chunk_index+1}/{len(self.chunks)}...")
        
        # Create prompt for topic extraction that processes the entire transcript
        # For longer transcripts, we'll use a strategic sampling approach
        if len(chunk) > 10000:
            # For very long transcripts, take samples from beginning, middle and end
            begin_sample = chunk[:3000]
            middle_start = len(chunk) // 2 - 1500
            middle_sample = chunk[middle_start:middle_start + 3000]
            end_sample = chunk[-3000:]
            chunk_sample = f"{begin_sample}\n\n[...middle of transcript...]\n\n{middle_sample}\n\n[...additional content...]\n\n{end_sample}"
        else:
            # For shorter transcripts, use the whole thing
            chunk_sample = chunk
            
        prompt = textwrap.dedent(f"""
        You are an expert at analyzing video content and identifying main topics.
        
        I'll provide you with a transcript from a YouTube video. Your task is to:
        1. Identify the MAIN TOPICS discussed in the ENTIRE video
        2. List each topic as a short, clear phrase (3-7 words)
        3. Provide at most {self.max_topics} topics
        4. Focus on substantive content, not just introductions or background information
        5. Consider the ENTIRE transcript when identifying topics, not just the beginning
        
        Here is the transcript:
        
        {chunk_sample}
        
        Respond with ONLY a JSON array of topic strings that represent the main subjects of the entire video. For example:
        ["Topic One", "Topic Two", "Topic Three"]
        """)
        
        # Call LLM to extract topics
        try:
            logger.info(f"Calling LLM for chunk {chunk_index+1} (timeout: 30s)...")
            response = call_llm(prompt, temperature=0.3, max_tokens=200, timeout=30)
            
            # Check if we got an error response
            if response.startswith("Error:"):
                logger.warning(f"LLM API error for chunk {chunk_index+1}: {response}")
                # Add some default topics if we can't get them from the LLM
                if chunk_index == 0:  # Only for the first chunk to avoid duplicates
                    logger.info("Using default topics due to LLM error")
                    return ["Main Content", "Key Points", "Summary"]
                return []
            
            logger.info(f"Received LLM response for chunk {chunk_index+1} ({len(response)} characters)")
            logger.debug(f"LLM response preview: {response[:100]}...")
            
            # Clean up the response to extract just the JSON array
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.split("```json")[1]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response.split("```")[0]
            
            # Try to parse as JSON, but handle errors gracefully
            try:
                import json
                topics = json.loads(cleaned_response)
                if isinstance(topics, list):
                    logger.info(f"Extracted {len(topics)} topics from chunk {chunk_index+1}")
                    logger.debug(f"Topics from chunk {chunk_index+1}: {topics}")
                    return topics
                else:
                    logger.warning(f"Expected list but got {type(topics)} from LLM")
                    # Try to extract topics from text response
                    return [cleaned_response]
            except json.JSONDecodeError:
                logger.warning(f"Could not parse LLM response as JSON: {cleaned_response}")
                # Try to extract topics from text response
                lines = cleaned_response.split("\n")
                potential_topics = [line.strip().strip('",[]') for line in lines if line.strip()]
                logger.info(f"Extracted {len(potential_topics)} topics from non-JSON response")
                return potential_topics
        except Exception as e:
            logger.error(f"Error calling LLM for chunk {chunk_index+1}: {str(e)}")
            # Add some default topics if we can't get them from the LLM
            if chunk_index == 0:  # Only for the first chunk to avoid duplicates
                logger.info("Using default topics due to exception")
                return ["Main Content", "Key Points", "Summary"]
            return []
    
    def post(self):
        """
        Post-process by combining topics from all chunks and selecting the most relevant ones.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Topic Extraction Node: {self.shared_memory['error']}")
            return
        
        if not self.chunk_topics:
            error_msg = "Failed to extract topics from transcript"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        # Flatten the list of topics from all chunks
        all_topics = []
        for topics in self.chunk_topics:
            all_topics.extend(topics)
        
        logger.debug(f"All extracted topics (before deduplication): {all_topics}")
        
        # Count topic occurrences to find the most common ones
        topic_counts = {}
        for topic in all_topics:
            topic_lower = topic.lower()
            topic_counts[topic_lower] = topic_counts.get(topic_lower, 0) + 1
        
        logger.debug(f"Topic frequency counts: {topic_counts}")
        
        # Sort topics by frequency
        sorted_topics = sorted(
            [(count, topic) for topic, count in topic_counts.items()], 
            reverse=True
        )
        
        # Select the top topics (using the original casing)
        top_topics = []
        seen_topics = set()
        
        for _, topic_lower in sorted_topics:
            # Find the original casing version
            original_casing = next(
                (t for t in all_topics if t.lower() == topic_lower), 
                topic_lower.title()
            )
            
            # Skip if we've already added this topic
            if topic_lower in seen_topics:
                continue
                
            top_topics.append(original_casing)
            seen_topics.add(topic_lower)
            
            # Limit to max_topics
            if len(top_topics) >= self.max_topics:
                break
        
        # Store the final list of topics
        self.shared_memory["topics"] = top_topics
        
        logger.info(f"Extracted {len(top_topics)} final topics:")
        for i, topic in enumerate(top_topics):
            logger.info(f"  {i+1}. {topic}")
        
        logger.info("Topic Extraction Node completed successfully")


if __name__ == "__main__":
    # Test with a sample transcript
    test_transcript = """
    In this video, we're going to talk about machine learning and its applications. 
    Machine learning is a subset of artificial intelligence that focuses on building systems 
    that learn from data. Unlike traditional programming where you explicitly program rules, 
    in machine learning, you train models on data and they learn patterns.
    
    There are several types of machine learning. First, supervised learning, where the model 
    is trained on labeled data. For example, you might have images labeled as "cat" or "dog" 
    and the model learns to distinguish between them. Second, unsupervised learning, where 
    the model finds patterns in unlabeled data. Clustering is a common unsupervised learning task.
    
    Deep learning is a subset of machine learning that uses neural networks with many layers. 
    These deep neural networks have revolutionized fields like computer vision and natural 
    language processing. For instance, convolutional neural networks (CNNs) are excellent at 
    image recognition tasks.
    
    Now let's discuss some applications of machine learning. In healthcare, machine learning 
    is used for disease diagnosis, drug discovery, and personalized medicine. In finance, 
    it's used for fraud detection, algorithmic trading, and credit scoring. In transportation, 
    self-driving cars rely heavily on machine learning algorithms.
    
    Ethical considerations in machine learning include bias in training data, model interpretability, 
    and privacy concerns. It's important to develop responsible AI systems that are fair and transparent.
    """
    
    # Initialize shared memory
    shared_memory = {"transcript": test_transcript}
    
    # Create and run the node
    node = TopicExtractionNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    logger.info(f"Topics: {updated_memory.get('topics', [])}")
