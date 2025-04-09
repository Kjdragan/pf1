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
from src.utils.generate_qa import generate_whole_content_qa
from src.utils.logger import logger

class TopicOrchestratorNode(BaseNode):
    """
    Node for orchestrating parallel processing of topics using Map-Reduce pattern.
    Maps topics to individual processors and reduces the results.
    """
    
    def __init__(self, shared_memory=None, max_workers=3, questions_per_topic=3, no_qa=False, whole_qa=False):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            max_workers (int): Maximum number of parallel workers for topic processing
            questions_per_topic (int): Number of questions to generate per topic
            no_qa (bool): Whether to disable Q&A generation entirely
            whole_qa (bool): Whether to generate comprehensive Q&A for the entire content
        """
        super().__init__(shared_memory)
        self.max_workers = max_workers
        self.questions_per_topic = questions_per_topic
        self.no_qa = no_qa
        self.whole_qa = whole_qa
        self.topics = []
        self.transcript = ""
        self.selected_rubric = None
        self.topic_results = {}
        logger.debug(f"TopicOrchestratorNode initialized with max_workers={max_workers}, questions_per_topic={questions_per_topic}, no_qa={no_qa}, whole_qa={whole_qa}")
    
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
        logger.debug(f"Q&A generation: {'Disabled' if self.no_qa else ('Whole-content' if self.whole_qa else 'Per-topic')}")
    
    def exec(self):
        """
        Execute Map-Reduce processing for topics.
        """
        if "error" in self.shared_memory:
            return
        
        logger.info("Starting Map-Reduce topic processing")
        
        # Dictionary to hold all Q&A pairs organized by topic
        qa_pairs = {}
        # Dictionary to hold all transformed content organized by topic
        transformed_content = {}
        
        # Process topics in parallel using a thread pool (Map phase)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Create a dictionary mapping futures to their topics
                futures = {
                    executor.submit(
                        self._process_topic, 
                        topic, 
                        self.transcript, 
                        self.selected_rubric,
                        self.questions_per_topic,
                        self.no_qa
                    ): topic for topic in self.topics
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(futures):
                    topic = futures[future]
                    try:
                        result = future.result()
                        self.topic_results[topic] = result
                        
                        # Extract Q&A pairs and transformed content
                        if not self.no_qa and not self.whole_qa:
                            qa_pairs[topic] = result.get("qa_pairs", [])
                        transformed_content[topic] = result.get("transformed_content", "")
                        
                        logger.info(f"Successfully processed topic: {topic}")
                    except Exception as e:
                        logger.exception(f"Error processing topic {topic}: {str(e)}")
                        # Continue with other topics on error
        
        except Exception as e:
            error_msg = f"Error in topic processing thread pool: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        # Handle whole content Q&A generation if enabled
        if not self.no_qa and self.whole_qa:
            logger.info("Generating comprehensive Q&A for the entire content")
            try:
                whole_content_qa = generate_whole_content_qa(self.topics, self.transcript, num_pairs=5)
                # Store as a special topic 'whole_content' to be rendered differently in HTML
                qa_pairs["whole_content"] = whole_content_qa
                logger.info(f"Successfully generated {len(whole_content_qa)} comprehensive Q&A pairs")
            except Exception as e:
                logger.exception(f"Error generating whole content Q&A: {str(e)}")
                # Continue even if whole content Q&A generation fails
        
        # Store results in shared memory (Reduce phase)
        self.shared_memory["qa_pairs"] = qa_pairs
        self.shared_memory["transformed_content"] = transformed_content
        
        logger.info(f"Processed {len(self.topic_results)} topics")
        logger.info(f"Generated {sum(len(pairs) for pairs in qa_pairs.values())} Q&A pairs")
        logger.info(f"Generated {len(transformed_content)} transformed content blocks")
    
    def _process_topic(self, topic, transcript, selected_rubric, questions_per_topic, no_qa):
        """
        Process a single topic using a TopicProcessorNode.
        
        Args:
            topic (str): The topic to process
            transcript (str): The video transcript
            selected_rubric (dict): The selected transformation rubric
            questions_per_topic (int): Number of questions to generate per topic
            no_qa (bool): Whether to disable Q&A generation
            
        Returns:
            dict: The processed results for the topic
        """
        logger.debug(f"Processing topic: {topic}")
        
        # Create an isolated shared memory for this topic processor
        topic_shared_memory = {
            "topic": topic,
            "transcript": transcript,
            "selected_rubric": selected_rubric,
            "questions_per_topic": questions_per_topic,
            "no_qa": no_qa
        }
        
        # Create and run a TopicProcessorNode for this topic
        processor = TopicProcessorNode(topic_shared_memory)
        result_memory = processor.run()
        
        return {
            "qa_pairs": result_memory.get("qa_pairs", []),
            "transformed_content": result_memory.get("transformed_content", "")
        }
    
    def post(self):
        """
        Post-process the topic results.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Topic Orchestrator Node: {self.shared_memory['error']}")
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
