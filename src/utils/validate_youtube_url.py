"""
Utility function to validate YouTube URLs and extract video IDs.
"""
import re
from urllib.parse import urlparse, parse_qs

def validate_youtube_url(url):
    """
    Validates if the given URL is a valid YouTube video URL and extracts the video ID.
    
    Args:
        url (str): The YouTube URL to validate
        
    Returns:
        tuple: (is_valid (bool), video_id (str))
    """
    if not url:
        return False, ""
    
    # Regular expression patterns for different YouTube URL formats
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    youtube_match = re.match(youtube_regex, url)
    
    if youtube_match:
        video_id = youtube_match.group(6)
        return True, video_id
    
    # Handle youtu.be format
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'youtu.be':
        video_id = parsed_url.path.lstrip('/')
        if len(video_id) == 11:
            return True, video_id
    
    # Handle youtube.com/watch?v= format
    if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            video_id = query_params['v'][0]
            if len(video_id) == 11:
                return True, video_id
    
    return False, ""


if __name__ == "__main__":
    # Test the function with some example URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.notayoutubeurl.com/watch?v=dQw4w9WgXcQ",
        "invalid_url"
    ]
    
    for url in test_urls:
        is_valid, video_id = validate_youtube_url(url)
        print(f"URL: {url}")
        print(f"Valid: {is_valid}")
        print(f"Video ID: {video_id}")
        print("-" * 40)
