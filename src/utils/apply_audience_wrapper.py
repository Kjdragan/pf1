"""
Utility to make subtle adjustments to content for target audience sophistication level.

This module applies light audience sophistication adjustments to transformed content,
ensuring it is appropriate for the target audience while preserving the core content
produced by the rubric transformation.
"""

import json
from enum import Enum
from typing import Dict, Any
from .call_llm import call_llm
from src.utils.logger import logger

class AudienceLevel(Enum):
    """Enum representing the available audience sophistication levels."""
    SOPHISTICATED = "sophisticated"
    GENERAL = "general"
    CHILD = "child"

# Audience level characteristics to guide the LLM
AUDIENCE_CHARACTERISTICS = {
    AudienceLevel.SOPHISTICATED.value: {
        "name": "Sophisticated",
        "description": "University-level education vocabulary, direct, occasional wit, analytical depth",
        "prompt": """
Make subtle adjustments for a sophisticated audience by:
- Refining vocabulary choices where appropriate (not changing core content)
- Preserving analytical depth and nuanced arguments
- Ensuring complex concepts remain appropriately challenging
- Making minimal adjustments to tone and style for sophisticated readers
- IMPORTANT: Preserve the original structure, organization, and most of the wording
"""
    },
    AudienceLevel.GENERAL.value: {
        "name": "General",
        "description": "Senior high school level (grades 11-12), moderate vocabulary, balanced complexity",
        "prompt": """
Make subtle adjustments for a senior high school audience (grades 11-12) by:
- Using vocabulary appropriate for advanced high school students (more sophisticated than middle school)
- Including appropriate academic terminology without over-simplification
- Maintaining reasonably complex sentence structures
- Using examples and explanations suitable for 16-18 year old students
- Assuming basic knowledge of civics, history, science, and current events
- IMPORTANT: Do not "talk down" to the audience or oversimplify complex concepts
- IMPORTANT: Preserve the original structure, organization, and most of the wording
"""
    },
    AudienceLevel.CHILD.value: {
        "name": "Child",
        "description": "Simplified language, concrete examples, used for ELI5 rubric",
        "prompt": """
Make subtle adjustments for a younger audience by:
- Lightly simplifying vocabulary only where necessary
- Adding minimal concrete examples or analogies only where helpful
- Making small adjustments to complex phrasing when needed
- IMPORTANT: Preserve the original structure, organization, and most of the wording
"""
    }
}

def apply_audience_wrapper(transformed_content: Dict[str, str], audience_level: str) -> Dict[str, str]:
    """
    Apply subtle audience sophistication adjustments to transformed content.
    
    This function makes minor adjustments at the edges of the content to ensure
    it's appropriate for the target audience, while preserving the core content
    produced by the rubric transformation.
    
    Args:
        transformed_content (Dict[str, str]): Dictionary mapping topics to their transformed content
        audience_level (str): The target audience level (must match an AudienceLevel enum value)
        
    Returns:
        Dict[str, str]: The content with subtle adjustments for the target audience
    """
    logger.info(f"Applying subtle {audience_level} audience adjustments to content")
    
    # Validate that audience_level is valid
    if audience_level not in [a.value for a in AudienceLevel]:
        logger.error(f"Invalid audience level: {audience_level}")
        audience_level = AudienceLevel.SOPHISTICATED.value
        logger.info(f"Falling back to default audience level: {audience_level}")
    
    audience_prompt = AUDIENCE_CHARACTERISTICS[audience_level]["prompt"]
    adjusted_content = {}
    
    # Apply subtle audience adjustments to each topic's transformed content
    for topic, content in transformed_content.items():
        adjusted_content[topic] = adjust_topic_for_audience(topic, content, audience_prompt)
    
    logger.info(f"Successfully applied subtle adjustments to {len(adjusted_content)} topics for {audience_level} audience level")
    return adjusted_content

def adjust_topic_for_audience(topic: str, content: str, audience_prompt: str) -> str:
    """
    Make subtle adjustments to a topic's content for the target audience level.
    
    Args:
        topic (str): The topic being adjusted
        content (str): The transformed content for the topic
        audience_prompt (str): The prompt guiding audience adjustment
        
    Returns:
        str: The content with subtle adjustments for the target audience
    """
    # Prepare the prompt for the LLM
    prompt = f"""
You are an expert content editor. Given a topic and its transformed content from a video,
make SUBTLE adjustments to ensure it's appropriate for the specified audience level.

IMPORTANT: This is NOT a full rewrite. The goal is to preserve 90-95% of the original 
content, making only minor adjustments at the edges for audience appropriateness.

Topic: {topic}

Content:
{content}

Adjustment Instructions:
{audience_prompt}

Make only minimal necessary adjustments while maintaining accuracy and the key points.
Preserve the original content, structure, and style as much as possible.
"""
    
    try:
        # Call the LLM to make subtle adjustments
        adjusted = call_llm(prompt)
        logger.debug(f"Successfully made subtle adjustments for audience level: {topic}")
        return adjusted
        
    except Exception as e:
        logger.exception(f"Error making audience adjustments for topic {topic}: {str(e)}")
        # Return the original content if adjustment fails
        return content

if __name__ == "__main__":
    # Simple test case
    test_transformed_content = {
        "Introduction to AI": """
## Introduction to AI

Artificial Intelligence represents the simulation of human cognitive processes by machines.
Key aspects include:
- The ability to learn from data
- Adaptation to new inputs
- Performance of human-like tasks

AI's significance stems from its potential to revolutionize industries through automation
and enhanced decision-making capabilities, ultimately addressing complex computational
challenges that were previously intractable.
""",
        "Machine Learning Basics": """
## Machine Learning Basics

Machine learning, a subset of AI, enables systems to automatically improve through experience.
The primary categorizations include:
1. Supervised learning - Learning from labeled examples
2. Unsupervised learning - Identifying patterns in unlabeled data
3. Reinforcement learning - Learning through reward-based feedback

These approaches form the foundation of contemporary AI applications across diverse domains.
"""
    }
    
    # Test applying subtle audience adjustments
    adjusted_content = apply_audience_wrapper(test_transformed_content, AudienceLevel.GENERAL.value)
    print(json.dumps(adjusted_content, indent=2))
