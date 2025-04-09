"""
Utility to generate Q&A pairs for topics extracted from video content.

This module takes topics and transcript data to generate relevant
question and answer pairs that enhance understanding of the video content.
"""

import json
from typing import Dict, List, Any
from .call_llm import call_llm
from src.utils.logger import logger

def generate_qa_pairs(topic: str, transcript: str, num_pairs: int = 3) -> List[Dict[str, str]]:
    """
    Generate Q&A pairs for a specific topic based on the video transcript.
    
    Args:
        topic (str): The topic to generate Q&A pairs for
        transcript (str): The video transcript content
        num_pairs (int): Number of Q&A pairs to generate (default: 3)
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing 'question' and 'answer' pairs
    """
    logger.info(f"Generating {num_pairs} Q&A pairs for topic: {topic}")
    
    # Create a sample of the transcript if it's too long
    transcript_sample = transcript[:5000] if len(transcript) > 5000 else transcript
    
    # Prepare a prompt for the LLM
    prompt = f"""
You are an expert educational content creator. Given a topic and video transcript,
generate {num_pairs} insightful question and answer pairs that:
1. Focus specifically on the topic "{topic}"
2. Cover key information present in the transcript
3. Progress from fundamental to more advanced understanding
4. Are clear, concise, and educational
5. PROVIDE ACTUAL ANSWERS based on the transcript, not placeholders

Video Transcript Sample:
{transcript_sample}

For the topic "{topic}", create {num_pairs} question and answer pairs.

IMPORTANT INSTRUCTIONS:
- PROVIDE SPECIFIC, DETAILED ANSWERS based on the transcript content
- Do NOT create placeholder or template answers like "This would explain..."
- Each answer should be 3-5 sentences with specific information from the transcript
- Focus on factual information that appears in the transcript
- If the transcript doesn't provide enough information, state what IS known

Your response MUST follow this exact format:
```json
[
  {{
    "question": "Clear, specific question about the topic",
    "answer": "Detailed, specific answer with information from the transcript."
  }},
  ...additional Q&A pairs...
]
```

CRITICAL REQUIREMENTS:
1. Start your response with ```json
2. End your response with ```
3. Use ONLY valid JSON with double quotes around keys and string values
4. Do not include any text outside the JSON code block
5. Do not use single quotes or trailing commas
6. If you're unsure about answering a question, provide an answer based on what IS in the transcript, rather than a placeholder
"""
    
    try:
        # Call the LLM to generate Q&A pairs
        response = call_llm(prompt)
        
        try:
            # Extract JSON from response if wrapped in markdown code blocks
            if "```json" in response and "```" in response.split("```json", 1)[1]:
                json_str = response.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in response:
                # Try to extract from any code block
                json_str = response.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                # Use the whole response if no code blocks are found
                json_str = response.strip()
            
            # Parse the JSON response
            qa_pairs = json.loads(json_str)
            logger.info(f"Successfully generated {len(qa_pairs)} Q&A pairs for topic: {topic}")
            
            # Validate the structure of each Q&A pair
            valid_qa_pairs = []
            for pair in qa_pairs:
                if isinstance(pair, dict) and "question" in pair and "answer" in pair:
                    valid_qa_pairs.append(pair)
                else:
                    logger.warning(f"Skipping invalid Q&A pair format: {pair}")
            
            if valid_qa_pairs:
                return valid_qa_pairs
            else:
                logger.warning(f"No valid Q&A pairs found for topic: {topic}")
                return get_fallback_qa_pairs(topic)
            
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM response as JSON for topic: {topic}. Error: {str(json_err)}")
            logger.debug(f"Response that failed parsing: {response[:200]}...")
            # Create a fallback response
            return get_fallback_qa_pairs(topic)
            
    except Exception as e:
        logger.exception(f"Error generating Q&A pairs for topic {topic}: {str(e)}")
        return get_fallback_qa_pairs(topic)

def generate_whole_content_qa(topics: List[str], transcript: str, num_pairs: int = 5) -> List[Dict[str, str]]:
    """
    Generate Q&A pairs for the entire content based on all topics and the transcript.
    This produces more comprehensive Q&A pairs that span across multiple topics.
    
    Args:
        topics (List[str]): List of all topics extracted from the video
        transcript (str): The complete video transcript content
        num_pairs (int): Number of Q&A pairs to generate (default: 5)
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing 'question' and 'answer' pairs
    """
    logger.info(f"Generating {num_pairs} comprehensive Q&A pairs spanning all topics")
    
    # Create a sample of the transcript if it's too long
    transcript_sample = transcript[:6000] if len(transcript) > 6000 else transcript
    
    # Format the topics list for inclusion in the prompt
    topics_text = json.dumps(topics)
    
    # Prepare a prompt for the LLM
    prompt = f"""
You are an expert educational content creator. Given a set of topics and a video transcript,
generate {num_pairs} comprehensive question and answer pairs that:
1. Cover the main themes across ALL topics
2. Address important connections between topics
3. Progress from basic to advanced understanding
4. Include specific information and details from the transcript
5. Provide substantial, informative answers (not templates or placeholders)

Video Topics: {topics_text}

Video Transcript Sample:
{transcript_sample}

Create {num_pairs} insightful question and answer pairs that span across these topics.

IMPORTANT INSTRUCTIONS:
- PROVIDE SPECIFIC, DETAILED ANSWERS based on the transcript content
- Each answer should be 4-6 sentences with specific information from the transcript
- Focus on cross-cutting themes that connect multiple topics
- Include factual details mentioned in the transcript, not generic information
- Address the most important aspects of the video content

Your response MUST follow this exact format:
```json
[
  {{
    "question": "Clear, specific question about important themes in the video",
    "answer": "Detailed, comprehensive answer with specific information from the transcript."
  }},
  ...additional Q&A pairs...
]
```

CRITICAL REQUIREMENTS:
1. Start your response with ```json
2. End your response with ```
3. Use ONLY valid JSON with double quotes around keys and string values
4. Do not include any text outside the JSON code block
5. Do not use single quotes or trailing commas
6. If you're unsure about answering a question, provide an answer based on what IS in the transcript, rather than a placeholder
"""
    
    try:
        # Call the LLM to generate Q&A pairs
        response = call_llm(prompt)
        
        try:
            # Extract JSON from response if wrapped in markdown code blocks
            if "```json" in response and "```" in response.split("```json", 1)[1]:
                json_str = response.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in response:
                # Try to extract from any code block
                json_str = response.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                # Use the whole response if no code blocks are found
                json_str = response.strip()
            
            # Parse the JSON response
            qa_pairs = json.loads(json_str)
            logger.info(f"Successfully generated {len(qa_pairs)} comprehensive Q&A pairs")
            
            # Validate the structure of each Q&A pair
            valid_qa_pairs = []
            for pair in qa_pairs:
                if isinstance(pair, dict) and "question" in pair and "answer" in pair:
                    valid_qa_pairs.append(pair)
                else:
                    logger.warning(f"Skipping invalid Q&A pair format: {pair}")
            
            if valid_qa_pairs:
                return valid_qa_pairs
            else:
                logger.warning("No valid comprehensive Q&A pairs found")
                return get_fallback_comprehensive_qa(topics)
            
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM response as JSON for comprehensive Q&A. Error: {str(json_err)}")
            logger.debug(f"Response that failed parsing: {response[:200]}...")
            # Create a fallback response
            return get_fallback_comprehensive_qa(topics)
            
    except Exception as e:
        logger.exception(f"Error generating comprehensive Q&A pairs: {str(e)}")
        return get_fallback_comprehensive_qa(topics)

def get_fallback_qa_pairs(topic: str) -> List[Dict[str, str]]:
    """
    Create fallback Q&A pairs when the LLM call fails.
    
    Args:
        topic (str): The topic to create fallback Q&A pairs for
        
    Returns:
        List[Dict[str, str]]: Basic fallback Q&A pairs
    """
    logger.info(f"Using fallback Q&A pairs for topic: {topic}")
    
    return [
        {
            "question": f"What is {topic}?",
            "answer": f"This would provide a definition and overview of {topic}."
        },
        {
            "question": f"Why is {topic} important?",
            "answer": f"This would explain the significance and applications of {topic}."
        },
        {
            "question": f"How does {topic} relate to other concepts in this video?",
            "answer": f"This would describe how {topic} connects to other ideas presented in the video."
        }
    ]

def get_fallback_comprehensive_qa(topics: List[str]) -> List[Dict[str, str]]:
    """
    Create fallback comprehensive Q&A pairs when the LLM call fails.
    
    Args:
        topics (List[str]): List of topics to reference in the fallback Q&A
        
    Returns:
        List[Dict[str, str]]: Basic fallback comprehensive Q&A pairs
    """
    logger.info("Using fallback comprehensive Q&A pairs")
    
    # Join topics with commas and 'and' for the last one
    if len(topics) > 1:
        topics_text = ", ".join(topics[:-1]) + ", and " + topics[-1]
    else:
        topics_text = topics[0] if topics else "the video topics"
    
    return [
        {
            "question": f"What are the key takeaways from this video?",
            "answer": f"This video covers several important topics including {topics_text}. The specific details would be extracted from the video transcript."
        },
        {
            "question": "How do these topics relate to each other?",
            "answer": "The topics in this video are interconnected through several themes. This answer would explain the relationships between the main ideas presented."
        },
        {
            "question": "What is the significance of these issues?",
            "answer": "These topics have important implications for several areas. This answer would provide context about why these issues matter."
        },
        {
            "question": "What are some practical applications of this information?",
            "answer": "The concepts discussed in this video have several practical applications. This answer would outline how this information might be applied."
        },
        {
            "question": "What further questions might arise from this topic?",
            "answer": "This video raises several important questions for further consideration. This answer would suggest areas for additional exploration."
        }
    ]

def process_topics_qa(topics: List[str], transcript: str, num_pairs_per_topic: int = 3) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate Q&A pairs for multiple topics from a video transcript.
    
    Args:
        topics (List[str]): List of topics to generate Q&A pairs for
        transcript (str): The video transcript content
        num_pairs_per_topic (int): Number of Q&A pairs to generate per topic (default: 3)
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary mapping topics to their Q&A pairs
    """
    logger.info(f"Processing Q&A generation for {len(topics)} topics")
    
    qa_results = {}
    
    for topic in topics:
        qa_results[topic] = generate_qa_pairs(topic, transcript, num_pairs_per_topic)
    
    logger.info(f"Completed Q&A generation for {len(qa_results)} topics")
    return qa_results

if __name__ == "__main__":
    # Simple test case
    test_transcript = """
    Machine learning is a subset of artificial intelligence that involves training 
    algorithms to recognize patterns in data. One of the most common applications 
    is in image recognition, where neural networks are trained to identify objects 
    in images. Neural networks are computational models inspired by the human brain's 
    structure, consisting of interconnected nodes or "neurons" that process information 
    in layers. Deep learning is an advanced approach to neural networks with many layers, 
    enabling more complex pattern recognition. Transfer learning is a technique where a 
    pre-trained model is adapted for a new task, saving computational resources and training time.
    """
    
    test_topics = ["Neural Networks", "Transfer Learning"]
    
    # Test generating Q&A pairs for multiple topics
    qa_results = process_topics_qa(test_topics, test_transcript)
    print(json.dumps(qa_results, indent=2))
