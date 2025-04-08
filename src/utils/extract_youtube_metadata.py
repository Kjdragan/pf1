"""
Utility function to extract metadata from YouTube videos.
"""
import requests
import json
import os
from datetime import datetime

def extract_youtube_metadata(video_id):
    """
    Extracts metadata from a YouTube video using the YouTube Data API.
    
    Args:
        video_id (str): The YouTube video ID
        
    Returns:
        dict: A dictionary containing video metadata (title, channel, duration, etc.)
    """
    # In a production environment, you would use an API key from environment variables
    # For this example, we'll use a placeholder
    # You would need to get your own API key from the Google Developer Console
    api_key = os.environ.get("YOUTUBE_API_KEY", "YOUR_API_KEY")
    
    # Base URL for YouTube Data API v3
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    
    # Parameters for the API request
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": video_id,
        "key": api_key
    }
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        data = response.json()
        
        # Check if the video exists
        if not data.get("items"):
            return {
                "error": "Video not found or API key invalid",
                "video_id": video_id
            }
        
        # Extract relevant metadata
        video_data = data["items"][0]
        snippet = video_data.get("snippet", {})
        content_details = video_data.get("contentDetails", {})
        statistics = video_data.get("statistics", {})
        
        # Format the duration (ISO 8601 format to human-readable)
        duration_iso = content_details.get("duration", "PT0S")
        # Simple conversion for common formats (not handling all ISO 8601 cases)
        hours = 0
        minutes = 0
        seconds = 0
        
        if "H" in duration_iso:
            hours = int(duration_iso.split("H")[0].split("PT")[1])
            duration_iso = duration_iso.split("H")[1]
        elif "PT" in duration_iso:
            duration_iso = duration_iso.split("PT")[1]
            
        if "M" in duration_iso:
            minutes = int(duration_iso.split("M")[0])
            duration_iso = duration_iso.split("M")[1]
            
        if "S" in duration_iso:
            seconds = int(duration_iso.split("S")[0])
        
        duration_str = ""
        if hours > 0:
            duration_str += f"{hours} hour{'s' if hours > 1 else ''} "
        if minutes > 0:
            duration_str += f"{minutes} minute{'s' if minutes > 1 else ''} "
        if seconds > 0 or (hours == 0 and minutes == 0):
            duration_str += f"{seconds} second{'s' if seconds > 1 else ''}"
        
        # Format the published date
        published_at = snippet.get("publishedAt", "")
        if published_at:
            try:
                published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                published_at = published_date.strftime("%B %d, %Y")
            except ValueError:
                pass
        
        # Construct the metadata dictionary
        metadata = {
            "video_id": video_id,
            "title": snippet.get("title", "Unknown Title"),
            "description": snippet.get("description", ""),
            "channel_name": snippet.get("channelTitle", "Unknown Channel"),
            "channel_id": snippet.get("channelId", ""),
            "published_at": published_at,
            "duration": duration_str,
            "duration_seconds": hours * 3600 + minutes * 60 + seconds,
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", ""),
        }
        
        return metadata
        
    except requests.exceptions.RequestException as e:
        # Handle request errors
        return {
            "error": f"API request error: {str(e)}",
            "video_id": video_id
        }
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        # Handle parsing errors
        return {
            "error": f"Data parsing error: {str(e)}",
            "video_id": video_id
        }


if __name__ == "__main__":
    # Test the function with an example video ID
    test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    metadata = extract_youtube_metadata(test_video_id)
    
    # Print the metadata in a readable format
    print(json.dumps(metadata, indent=2))
