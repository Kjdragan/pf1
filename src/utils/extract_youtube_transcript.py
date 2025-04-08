"""
Utility function to extract transcript from YouTube videos.
"""
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def extract_youtube_transcript(video_id):
    """
    Extracts the transcript/captions from a YouTube video.
    
    Args:
        video_id (str): The YouTube video ID
        
    Returns:
        str: The full transcript text or an error message
    """
    try:
        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first, fall back to other languages if needed
        try:
            transcript = transcript_list.find_transcript(['en'])
        except NoTranscriptFound:
            # If no English transcript is found, use the first available one
            transcript = transcript_list.find_transcript([])
            
            # If it's not in English, try to translate it
            if transcript.language_code != 'en':
                transcript = transcript.translate('en')
        
        # Fetch the transcript data
        transcript_data = transcript.fetch()
        
        # Combine all transcript segments into a single text
        full_transcript = ""
        for segment in transcript_data:
            # The segment is a dictionary with 'text', 'start', and 'duration' keys
            if isinstance(segment, dict) and 'text' in segment:
                text = segment['text']
            else:
                # Handle FetchedTranscriptSnippet objects
                text = segment.text if hasattr(segment, 'text') else str(segment)
                
            # Add a space if the text doesn't end with punctuation
            if text and text[-1] not in '.!?':
                text += ' '
            full_transcript += text
        
        return full_transcript.strip()
        
    except TranscriptsDisabled:
        return "Error: Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "Error: No transcript found for this video."
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"


if __name__ == "__main__":
    # Test the function with an example video ID
    test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    transcript = extract_youtube_transcript(test_video_id)
    
    # Print the first 500 characters of the transcript
    print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
