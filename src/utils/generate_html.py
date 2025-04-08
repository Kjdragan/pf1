"""
Utility function to generate HTML output for the YouTube video summary.
"""
import html

def generate_html(summary_data):
    """
    Generates an HTML page to visualize the YouTube video summary.
    
    Args:
        summary_data (dict): A dictionary containing all the processed information
            - video_id (str): YouTube video ID
            - metadata (dict): Video metadata
            - topics (list): List of extracted topics
            - qa_pairs (dict): Q&A pairs organized by topic
            - eli5_content (dict): Child-friendly explanations
            
    Returns:
        str: HTML content as a string
    """
    if not summary_data:
        return "<html><body><h1>Error: No summary data provided</h1></body></html>"
    
    video_id = summary_data.get("video_id", "")
    metadata = summary_data.get("metadata", {})
    topics = summary_data.get("topics", [])
    qa_pairs = summary_data.get("qa_pairs", {})
    eli5_content = summary_data.get("eli5_content", {})
    
    # Escape HTML special characters to prevent XSS
    title = html.escape(metadata.get("title", "YouTube Video Summary"))
    channel = html.escape(metadata.get("channel_name", "Unknown Channel"))
    duration = html.escape(metadata.get("duration", ""))
    published_at = html.escape(metadata.get("published_at", ""))
    thumbnail_url = metadata.get("thumbnail_url", "")
    
    # Generate the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Summary</title>
    <style>
        :root {{
            --primary-color: #ff5252;
            --secondary-color: #3f51b5;
            --background-color: #f9f9f9;
            --card-color: #ffffff;
            --text-color: #333333;
            --border-radius: 10px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        body {{
            font-family: 'Comic Sans MS', 'Chalkboard SE', 'Arial', sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: var(--primary-color);
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        h2 {{
            color: var(--secondary-color);
            font-size: 1.8rem;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        
        h3 {{
            color: var(--primary-color);
            font-size: 1.5rem;
        }}
        
        .video-info {{
            display: flex;
            align-items: center;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .video-thumbnail {{
            flex: 0 0 280px;
            margin-right: 20px;
        }}
        
        .video-thumbnail img {{
            width: 100%;
            border-radius: var(--border-radius);
        }}
        
        .video-details {{
            flex: 1;
        }}
        
        .topic-card {{
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .qa-section {{
            background-color: rgba(63, 81, 181, 0.1);
            border-radius: var(--border-radius);
            padding: 15px;
            margin-top: 15px;
        }}
        
        .question {{
            font-weight: bold;
            color: var(--secondary-color);
            margin-bottom: 5px;
        }}
        
        .answer {{
            margin-bottom: 15px;
            padding-left: 15px;
            border-left: 3px solid var(--primary-color);
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            font-size: 0.9rem;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .video-info {{
                flex-direction: column;
            }}
            
            .video-thumbnail {{
                margin-right: 0;
                margin-bottom: 20px;
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎬 Kid-Friendly Video Summary 🎬</h1>
            <p>Here's a simple explanation of what this video is all about!</p>
        </header>
        
        <div class="video-info">
            <div class="video-thumbnail">
                <img src="{thumbnail_url}" alt="{title}" onerror="this.src='https://via.placeholder.com/280x158?text=No+Thumbnail'">
                <p style="text-align: center; margin-top: 10px;">
                    <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" style="text-decoration: none; color: var(--primary-color);">
                        Watch on YouTube
                    </a>
                </p>
            </div>
            <div class="video-details">
                <h2>{title}</h2>
                <p><strong>Channel:</strong> {channel}</p>
                <p><strong>Duration:</strong> {duration}</p>
                <p><strong>Published:</strong> {published_at}</p>
            </div>
        </div>
"""
    
    # Add topics and their content
    for i, topic in enumerate(topics):
        topic_escaped = html.escape(topic)
        topic_id = f"topic-{i+1}"
        
        # Get ELI5 explanation for this topic
        eli5_explanation = html.escape(eli5_content.get(topic, ""))
        
        # Get Q&A pairs for this topic
        topic_qa_pairs = qa_pairs.get(topic, [])
        
        html_content += f"""
        <h2 id="{topic_id}">Topic {i+1}: {topic_escaped}</h2>
        <div class="topic-card">
            <p>{eli5_explanation}</p>
            
            <div class="qa-section">
                <h3>Questions & Answers</h3>
"""
        
        # Add Q&A pairs
        if topic_qa_pairs:
            for qa in topic_qa_pairs:
                question = html.escape(qa.get("question", ""))
                answer = html.escape(qa.get("answer", ""))
                
                html_content += f"""
                <div class="question">Q: {question}</div>
                <div class="answer">A: {answer}</div>
"""
        else:
            html_content += """
                <p>No questions available for this topic.</p>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    # Close the HTML document
    html_content += """
        <footer>
            <p>This summary was created by YouTube Video Summarizer</p>
        </footer>
    </div>
</body>
</html>
"""
    
    return html_content


if __name__ == "__main__":
    # Test the function with sample data
    test_data = {
        "video_id": "dQw4w9WgXcQ",
        "metadata": {
            "title": "Rick Astley - Never Gonna Give You Up",
            "channel_name": "Rick Astley",
            "duration": "3 minutes 33 seconds",
            "published_at": "October 25, 2009",
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
        },
        "topics": [
            "Music Video Plot",
            "Song Lyrics",
            "Cultural Impact"
        ],
        "qa_pairs": {
            "Music Video Plot": [
                {
                    "question": "What happens in the music video?",
                    "answer": "Rick dances and sings in different locations with backup dancers."
                },
                {
                    "question": "What is Rick wearing?",
                    "answer": "Rick is wearing a long coat and has styled hair."
                }
            ],
            "Song Lyrics": [
                {
                    "question": "What is the main message of the song?",
                    "answer": "The song is about commitment and never letting someone down."
                }
            ],
            "Cultural Impact": [
                {
                    "question": "Why is this song famous on the internet?",
                    "answer": "It became an internet prank called 'Rickrolling' where people are tricked into clicking links to this video."
                }
            ]
        },
        "eli5_content": {
            "Music Video Plot": "In this video, a man named Rick is dancing and singing. He moves his arms and legs in a funny way that people like to copy. He sings in different places like a stage and outside.",
            "Song Lyrics": "Rick is singing about being a good friend. He promises to always be there for someone special and never make them sad or tell lies. It's like when you promise to always be nice to your best friend.",
            "Cultural Impact": "This song became super famous because people on the internet started using it as a funny joke. They would trick their friends by saying 'click here for something cool' but the link would take them to this song instead. This joke is called 'Rickrolling'."
        }
    }
    
    html_output = generate_html(test_data)
    
    # Save the HTML to a file for testing
    with open("test_summary.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    
    print("HTML generated and saved to test_summary.html")
