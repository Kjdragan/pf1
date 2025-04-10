"""
Utility to transform content according to a selected rubric.

This module takes content and applies a transformation according to the 
specified rubric type, structuring and formatting the information appropriately.
"""

import json
from enum import Enum
from typing import Dict, List, Any
from .call_llm import call_llm
from src.utils.logger import logger

class RubricType(Enum):
    """Enum representing the available document transformation rubrics."""
    INSIGHTFUL_CONVERSATIONAL = "insightful_conversational"
    ANALYTICAL_NARRATIVE = "analytical_narrative" 
    EDUCATIONAL_EXTRACTION = "educational_extraction"
    STRUCTURED_DIGEST = "structured_digest"
    EMOTION_CONTEXT_RICH = "emotion_context_rich"
    TOP_N_KNOWLEDGE = "top_n_knowledge"
    CHECKLIST_ACTIONABLE = "checklist_actionable"
    CONTRARIAN_INSIGHTS = "contrarian_insights"
    KEY_QUOTES = "key_quotes"
    ELI5 = "eli5"

# Default knowledge augmentation levels for each rubric (1-10 scale)
# 1: Pure extraction/summarization - only information explicitly stated in the video
# 5: Balanced approach - mostly video content with some contextual information
# 10: Heavy augmentation - extensive external knowledge and analysis
DEFAULT_KNOWLEDGE_LEVELS = {
    RubricType.INSIGHTFUL_CONVERSATIONAL.value: 5,
    RubricType.ANALYTICAL_NARRATIVE.value: 7, 
    RubricType.EDUCATIONAL_EXTRACTION.value: 6,
    RubricType.STRUCTURED_DIGEST.value: 4,
    RubricType.EMOTION_CONTEXT_RICH.value: 3,
    RubricType.TOP_N_KNOWLEDGE.value: 5,
    RubricType.CHECKLIST_ACTIONABLE.value: 6,
    RubricType.CONTRARIAN_INSIGHTS.value: 8,
    RubricType.KEY_QUOTES.value: 1,
    RubricType.ELI5.value: 5
}

# Rubric prompts that guide the LLM in applying each transformation style
RUBRIC_PROMPTS = {
    RubricType.INSIGHTFUL_CONVERSATIONAL.value: """
Transform the content into an insightful conversational summary that:
- Maintains a conversational tone and authentic voice
- Uses moderate compression while preserving key details
- Retains important quotes and analogies
- Balances information density with readability
""",
    RubricType.ANALYTICAL_NARRATIVE.value: """
Transform the content into an analytical narrative that:
- Preserves core arguments and key points
- Adds analytical commentary clearly separate from original ideas
- Uses phrases like "This suggests that..." or "This implies..."
- Maintains sophisticated language and logical flow
""",
    RubricType.EDUCATIONAL_EXTRACTION.value: """
Transform the content into an in-depth educational extraction that:
- Uses lower compression to preserve educational value
- Maintains definitions, concepts, and examples with original phrasing
- Structures content in a logical learning sequence
- Preserves nuance and complexity for educational purposes
""",
    RubricType.STRUCTURED_DIGEST.value: """
Transform the content into a structured knowledge digest that:
- Uses high compression for concise knowledge delivery
- Organizes information in clear bullet points and sections
- Uses descriptive headings for each section
- Prioritizes insights and key takeaways
""",
    RubricType.EMOTION_CONTEXT_RICH.value: """
Transform the content into an emotion and context-rich narration that:
- Captures emotional depth and authentic voice
- Emphasizes personal narratives and experiences
- Preserves nuanced context and emotional tone
- Connects ideas through emotional threads
""",
    RubricType.TOP_N_KNOWLEDGE.value: """
Transform the content into a "Top N" knowledge extraction that:
- Presents information as enumerated, prioritized lists
- Begins points with "One key insight is..." or similar phrases
- Ranks information by importance or relevance
- Maintains sophisticated language while being concise
""",
    RubricType.CHECKLIST_ACTIONABLE.value: """
Transform the content into a checklist or actionable summary that:
- Structures information as task-oriented checklists
- Begins points with action verbs
- Focuses on practical application of knowledge
- Organizes steps in a logical sequence
""",
    RubricType.CONTRARIAN_INSIGHTS.value: """
Transform the content into contrarian insights (myth-busting) that:
- Identifies and clarifies misconceptions explicitly
- Structures content as "Myth: X" and "Reality: Y"
- Uses direct language to address common misunderstandings
- Provides evidence or reasoning for the corrections
""",
    RubricType.KEY_QUOTES.value: """
Transform the content into key quotes or notable statements that:
- Extracts direct quotes preserving exact original wording
- Uses minimal compression to maintain impact
- Provides brief context for each quote
- Selects high-impact or insight-rich statements
""",
    RubricType.ELI5.value: """
Transform the content into an ELI5 (Explain Like I'm Five) format that:
- Uses simple language appropriate for beginners
- Employs basic analogies and concrete examples
- Breaks down complex concepts into simple components
- Avoids jargon and technical terminology
"""
}

def apply_rubric(content: Dict[str, Any], rubric_type: str, knowledge_level: int = None) -> Dict[str, Any]:
    """
    Transform content according to the selected rubric.
    
    Args:
        content (Dict): The content to transform, should contain topics and either qa_pairs or transcript
        rubric_type (str): The rubric type to apply (must match a RubricType enum value)
        knowledge_level (int, optional): Level of external knowledge to incorporate (1-10)
            1: Pure extraction - only information explicitly stated in the video
            10: Heavy augmentation - extensive external knowledge and analysis
        
    Returns:
        Dict: The transformed content
    """
    logger.info(f"Applying {rubric_type} rubric to content")
    
    # Validate that rubric_type is valid
    if rubric_type not in [r.value for r in RubricType]:
        logger.error(f"Invalid rubric type: {rubric_type}")
        rubric_type = RubricType.INSIGHTFUL_CONVERSATIONAL.value
        logger.info(f"Falling back to default rubric: {rubric_type}")
    
    # Use default knowledge level if not specified
    if knowledge_level is None:
        knowledge_level = DEFAULT_KNOWLEDGE_LEVELS.get(rubric_type, 5)
    else:
        # Ensure knowledge_level is within valid range
        knowledge_level = max(1, min(10, knowledge_level))
    
    logger.info(f"Using knowledge augmentation level: {knowledge_level}/10")
    
    transformed_content = {}
    topics = content.get("topics", [])
    qa_pairs = content.get("qa_pairs", {})
    transcript = content.get("transcript", "")
    
    # Apply the rubric to each topic
    for topic in topics:
        if topic in qa_pairs:
            # Use Q&A pairs if available
            transformed_content[topic] = transform_topic(topic, qa_pairs[topic], rubric_type, knowledge_level)
        elif transcript:
            # Use transcript directly if no Q&A pairs but transcript is available
            transformed_content[topic] = transform_topic_from_transcript(topic, transcript, rubric_type, knowledge_level)
        else:
            logger.warning(f"Missing both Q&A pairs and transcript for topic: {topic}")
    
    logger.info(f"Successfully transformed {len(transformed_content)} topics using {rubric_type} rubric")
    return {"transformed_content": transformed_content}

def transform_topic(topic: str, qa_pairs: List[Dict], rubric_type: str, knowledge_level: int) -> str:
    """
    Transform a single topic's Q&A pairs according to the selected rubric.
    
    Args:
        topic (str): The topic to transform
        qa_pairs (List[Dict]): List of Q&A pairs for the topic
        rubric_type (str): The rubric type to apply
        knowledge_level (int): Level of external knowledge to incorporate (1-10)
        
    Returns:
        str: The transformed content for the topic
    """
    # Prepare the content in a structured format for the LLM
    formatted_qa = "\n\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs])
    
    # Get the appropriate prompt for the selected rubric
    rubric_prompt = RUBRIC_PROMPTS[rubric_type]
    
    # Create knowledge level guidance based on the level
    knowledge_guidance = get_knowledge_level_guidance(knowledge_level)
    
    # Prepare the prompt for the LLM
    prompt = f"""
You are an expert content transformer. Given a topic and its Q&A pairs from a video,
transform this content according to the specified rubric.

Topic: {topic}

Q&A Content:
{formatted_qa}

Transformation Rubric Instructions:
{rubric_prompt}

Knowledge Augmentation Level: {knowledge_level}/10
{knowledge_guidance}

Transform the content while maintaining accuracy and the original meaning.
Keep your response focused on the transformed content only.
"""
    
    try:
        # Call the LLM to transform the content
        transformed = call_llm(prompt)
        logger.debug(f"Successfully transformed topic: {topic}")
        return transformed
        
    except Exception as e:
        logger.exception(f"Error transforming topic {topic}: {str(e)}")
        # Return a fallback transformation
        return f"## {topic}\n\n" + "\n\n".join([f"**{qa['question']}**\n\n{qa['answer']}" for qa in qa_pairs])

def transform_topic_from_transcript(topic: str, transcript: str, rubric_type: str, knowledge_level: int) -> str:
    """
    Transform a single topic using the transcript directly (without Q&A pairs).
    
    Args:
        topic (str): The topic to transform
        transcript (str): The video transcript
        rubric_type (str): The rubric type to apply
        knowledge_level (int): Level of external knowledge to incorporate (1-10)
        
    Returns:
        str: The transformed content for the topic
    """
    # Get the appropriate prompt for the selected rubric
    rubric_prompt = RUBRIC_PROMPTS[rubric_type]
    
    # Create knowledge level guidance based on the level
    knowledge_guidance = get_knowledge_level_guidance(knowledge_level)
    
    # Prepare the prompt for the LLM
    prompt = f"""
You are an expert content transformer. Given a topic and a video transcript,
transform this content according to the specified rubric.

Topic: {topic}

Video Transcript:
{transcript[:2000]}... [transcript continues]

Transformation Rubric Instructions:
{rubric_prompt}

Knowledge Augmentation Level: {knowledge_level}/10
{knowledge_guidance}

Focus on extracting and transforming content related to the topic '{topic}' from the transcript.
Transform the content while maintaining accuracy and the original meaning.
Keep your response focused on the transformed content only.
"""
    
    try:
        # Call the LLM to transform the content
        transformed = call_llm(prompt)
        logger.debug(f"Successfully transformed topic from transcript: {topic}")
        return transformed
        
    except Exception as e:
        logger.exception(f"Error transforming topic {topic} from transcript: {str(e)}")
        # Return a fallback transformation
        return f"## {topic}\n\nUnable to transform content for this topic. Please check the transcript for information related to {topic}."

def get_knowledge_level_guidance(level: int) -> str:
    """
    Generate guidance text for the specified knowledge augmentation level.
    
    Args:
        level (int): Knowledge augmentation level (1-10)
        
    Returns:
        str: Guidance text for the LLM
    """
    if level <= 2:
        return """
IMPORTANT: Use ONLY information explicitly stated in the video content.
- Do NOT add any external knowledge, context, or analysis
- Focus exclusively on summarizing/organizing what was directly said or shown
- If the content lacks information on a topic, simply note that it wasn't covered
- NEVER make assumptions or fill in gaps with external knowledge
"""
    elif level <= 4:
        return """
IMPORTANT: Primarily use information from the video content (approximately 80-90%).
- Add minimal external context ONLY when necessary to clarify concepts mentioned in the video
- Clearly mark any added context with [Context: ...]
- Focus on organizing and presenting what was actually in the video
- Keep external additions brief and only for clarification purposes
"""
    elif level <= 6:
        return """
IMPORTANT: Balance video content (approximately 70%) with helpful contextual information.
- Add moderate external context to enhance understanding of concepts in the video
- Clearly distinguish between video content and added information
- Use phrases like "Additionally, ..." or "For context, ..." to introduce external knowledge
- Ensure the video's core content remains the primary focus
"""
    elif level <= 8:
        return """
IMPORTANT: Enhance video content (approximately 50-60%) with substantial contextual information.
- Add significant external knowledge to place the video in broader context
- Use clear section breaks or formatting to distinguish video content from added information
- Develop concepts mentioned briefly in the video with additional explanation
- Create a comprehensive resource that extends beyond the original video
"""
    else:  # 9-10
        return """
IMPORTANT: Create a comprehensive resource using the video as a starting point.
- Extensively augment the video content (which may be 30-40% of the final output)
- Add detailed explanations, examples, and related concepts not mentioned in the video
- Organize content logically, which may differ from the video's structure
- Develop a thorough treatment of the topic that goes well beyond the original video
- Always maintain a section that summarizes what was actually in the original video
"""

if __name__ == "__main__":
    # Simple test case
    test_content = {
        "topics": ["Introduction to AI", "Machine Learning Basics"],
        "qa_pairs": {
            "Introduction to AI": [
                {"question": "What is AI?", "answer": "AI is the simulation of human intelligence in machines."},
                {"question": "Why is AI important?", "answer": "AI enables automation and can solve complex problems."}
            ],
            "Machine Learning Basics": [
                {"question": "What is machine learning?", "answer": "Machine learning is a subset of AI that enables systems to learn from data."},
                {"question": "What types of machine learning exist?", "answer": "The main types are supervised, unsupervised, and reinforcement learning."}
            ]
        }
    }
    
    # Test applying a rubric
    transformed = apply_rubric(test_content, RubricType.STRUCTURED_DIGEST.value)
    print(json.dumps(transformed, indent=2))
