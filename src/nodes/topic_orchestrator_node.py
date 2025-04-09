"""
Topic Processing Orchestrator Node for YouTube Video Summarizer.
Implements a Map-Reduce approach for parallel topic processing.
"""
import sys
import os
from typing import List, Dict, Any
import concurrent.futures

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.nodes.topic_processor_node import TopicProcessorNode
from src.utils.logger import logger

class TopicOrchestratorNode(BaseNode):
    """
    Node for orchestrating parallel processing of topics using Map-Reduce pattern.
    Maps topics to individual processors and reduces the results.
    """
    
    def __init__(self, shared_memory=None, max_workers=3, questions_per_topic=3):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            max_workers (int): Maximum number of parallel workers for topic processing
            questions_per_topic (int): Number of questions to generate per topic
        """
        super().__init__(shared_memory)
        self.max_workers = max_workers
        self.questions_per_topic = questions_per_topic
        self.topics = []
        self.transcript = ""
        self.selected_rubric = None
        self.topic_results = {}
        logger.debug(f"TopicOrchestratorNode initialized with max_workers={max_workers}, questions_per_topic={questions_per_topic}")
    
    def prep(self):
        """
        Prepare for execution by checking if topics, transcript, and selected rubric exist in shared memory.
        """
        if "topics" not in self.shared_memory:
            error_msg = "Topics not found in shared memory"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if "transcript" not in self.shared_memory:
            error_msg = "Transcript not found in shared memory"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if "selected_rubric" not in self.shared_memory:
            error_msg = "Selected rubric not found in shared memory"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping Topic Orchestration due to previous error: {self.shared_memory['error']}")
            return
        
        self.topics = self.shared_memory["topics"]
        self.transcript = self.shared_memory["transcript"]
        self.selected_rubric = self.shared_memory["selected_rubric"]
        
        topics_count = len(self.topics)
        # Adjust max_workers if there are fewer topics than workers
        self.max_workers = min(self.max_workers, topics_count)
        logger.info(f"Preparing to process {topics_count} topics with {self.max_workers} parallel workers")
        logger.debug(f"Topics to process: {self.topics}")
        logger.debug(f"Selected rubric: {self.selected_rubric['name']}")
    
    def exec(self):
        """
        Execute Map-Reduce processing for topics.
        """
        if "error" in self.shared_memory:
            return
        
        # Map phase: Process all topics in parallel
        self._map_phase()
        
        # Reduce phase: Combine results
        self._reduce_phase()
    
    def _map_phase(self):
        """
        Map phase: Process all topics in parallel using a thread pool.
        """
        logger.info(f"Starting Map phase with {self.max_workers} workers for {len(self.topics)} topics")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all topics for processing
            future_to_topic = {
                executor.submit(self._process_topic, topic): topic 
                for topic in self.topics
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    result = future.result()
                    self.topic_results[topic] = result
                    logger.info(f"Completed processing for topic: {topic}")
                except Exception as e:
                    logger.error(f"Error processing topic '{topic}': {str(e)}")
                    self.shared_memory["error"] = f"Error processing topic '{topic}': {str(e)}"
    
    def _process_topic(self, topic):
        """
        Process a single topic using a TopicProcessorNode.
        
        Args:
            topic (str): The topic to process
            
        Returns:
            dict: The processing result
        """
        logger.info(f"Processing topic: {topic}")
        
        # Create a topic processor node
        processor = TopicProcessorNode(
            topic=topic,
            transcript=self.transcript,
            selected_rubric=self.selected_rubric,
            questions_per_topic=self.questions_per_topic
        )
        
        return processor.run()["topic_results"][topic]
    
    def _reduce_phase(self):
        """
        Reduce phase: Combine results from all topic processors.
        """
        if "error" in self.shared_memory:
            return
            
        logger.info(f"Starting Reduce phase with {len(self.topic_results)} topic results")
        
        # Initialize the combined results
        qa_pairs = {}
        transformed_content = {}
        
        # Combine results from all topics
        for topic, result in self.topic_results.items():
            # Add Q&A pairs
            qa_pairs[topic] = result.get("qa_pairs", [])
            
            # Add transformed content
            transformed_content[topic] = result.get("transformed_content", "")
        
        # Store the combined results in shared memory
        self.shared_memory["qa_pairs"] = qa_pairs
        self.shared_memory["transformed_content"] = transformed_content
        self.shared_memory["topic_results"] = self.topic_results
        
        # Log summary of combined results
        total_qa_pairs = sum(len(pairs) for pairs in qa_pairs.values())
        logger.info(f"Reduce phase complete: Combined {total_qa_pairs} Q&A pairs across {len(qa_pairs)} topics")
    
    def post(self):
        """
        Post-process and check for errors.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Topic Orchestrator Node: {self.shared_memory['error']}")
            return
        
        if not self.topic_results:
            error_msg = "No topic results were generated"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        logger.info("Topic Orchestrator Node completed successfully")
        logger.info(f"Processed {len(self.topic_results)} topics using Map-Reduce pattern")


if __name__ == "__main__":
    # Test with sample topics and transcript
    test_topics = ["Machine Learning Basics", "Types of Machine Learning"]
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
    """
    
    # Test rubric
    test_rubric = {
        "rubric_id": "structured_digest",
        "name": "Structured Knowledge Digest",
        "confidence": 85,
        "description": "High compression, concise knowledge delivery, organized bullet points, clear headings"
    }
    
    # Initialize shared memory
    shared_memory = {
        "topics": test_topics,
        "transcript": test_transcript,
        "selected_rubric": test_rubric
    }
    
    # Create and run the node
    node = TopicOrchestratorNode(shared_memory, max_workers=2)
    updated_memory = node.run()
    
    # Print the results if no error
    if "error" not in updated_memory:
        print("\nShared Memory after processing:")
        
        # Print Q&A pairs
        qa_pairs = updated_memory.get("qa_pairs", {})
        for topic, pairs in qa_pairs.items():
            print(f"\nTopic: {topic}")
            print(f"Q&A Pairs: {len(pairs)}")
            for i, qa in enumerate(pairs):
                print(f"  Q{i+1}: {qa.get('question', '')}")
                print(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
        
        # Print transformed content
        transformed_content = updated_memory.get("transformed_content", {})
        for topic, content in transformed_content.items():
            print(f"\nTransformed Content for {topic}:")
            print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print(f"Error: {updated_memory['error']}")
