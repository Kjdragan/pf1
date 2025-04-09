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
            - transformed_content (dict): Transformed content based on selected rubric
            - selected_rubric (dict): Information about the selected transformation rubric
            - audience_level (str): Selected audience sophistication level
            
    Returns:
        str: HTML content as a string
    """
    if not summary_data:
        return "<html><body><h1>Error: No summary data provided</h1></body></html>"
    
    video_id = summary_data.get("video_id", "")
    metadata = summary_data.get("metadata", {})
    topics = summary_data.get("topics", [])
    qa_pairs = summary_data.get("qa_pairs", {})
    transformed_content = summary_data.get("transformed_content", {})
    selected_rubric = summary_data.get("selected_rubric", {})
    audience_level = summary_data.get("audience_level", "sophisticated")
    
    # Check if we have whole content Q&A pairs
    has_whole_content_qa = "whole_content" in qa_pairs
    
    # Escape HTML special characters to prevent XSS
    title = html.escape(metadata.get("title", "YouTube Video Summary"))
    channel = html.escape(metadata.get("channel_name", "Unknown Channel"))
    duration = html.escape(metadata.get("duration", ""))
    published_at = html.escape(metadata.get("published_at", ""))
    thumbnail_url = metadata.get("thumbnail_url", "")
    rubric_name = html.escape(selected_rubric.get("name", "Custom Transformation"))
    
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
            font-family: 'Arial', sans-serif;
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
            margin: 25px 0 15px;
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: 5px;
        }}
        
        h3 {{
            color: var(--text-color);
            font-size: 1.4rem;
            margin: 20px 0 10px;
        }}
        
        .video-info {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
            background-color: var(--card-color);
            padding: 20px;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
        }}
        
        .video-thumbnail {{
            flex: 0 0 300px;
            max-width: 100%;
        }}
        
        .video-thumbnail img {{
            width: 100%;
            border-radius: var(--border-radius);
        }}
        
        .video-details {{
            flex: 1;
            min-width: 300px;
        }}
        
        .meta-item {{
            margin-bottom: 10px;
        }}
        
        .meta-label {{
            font-weight: bold;
            color: var(--secondary-color);
        }}
        
        .topic-card {{
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: var(--box-shadow);
        }}
        
        .qa-pair {{
            margin-bottom: 20px;
            border-left: 3px solid var(--primary-color);
            padding-left: 15px;
        }}
        
        .question {{
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 5px;
        }}
        
        .answer {{
            margin-left: 15px;
        }}
        
        .content-block {{
            background-color: #f5f5f5;
            border-radius: var(--border-radius);
            padding: 15px;
            margin-top: 20px;
            border-left: 3px solid var(--secondary-color);
        }}
        
        .rubric-badge {{
            display: inline-block;
            background-color: var(--secondary-color);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }}
        
        .audience-badge {{
            display: inline-block;
            background-color: var(--primary-color);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9rem;
            margin-left: 10px;
        }}
        
        .whole-content-qa {{
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            padding: 20px;
            margin: 30px 0;
            box-shadow: var(--box-shadow);
            border-top: 4px solid var(--primary-color);
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="rubric-badge">{rubric_name}</div>
            <div class="audience-badge">Audience: {audience_level.capitalize()}</div>
        </header>
        
        <div class="video-info">
            <div class="video-thumbnail">
                <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">
                    <img src="{thumbnail_url}" alt="{title}">
                </a>
            </div>
            <div class="video-details">
                <div class="meta-item">
                    <span class="meta-label">Channel:</span> {channel}
                </div>
                <div class="meta-item">
                    <span class="meta-label">Duration:</span> {duration}
                </div>
                <div class="meta-item">
                    <span class="meta-label">Published:</span> {published_at}
                </div>
                <div class="meta-item">
                    <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">Watch on YouTube</a>
                </div>
            </div>
        </div>
"""

    # Add whole content Q&A section if available
    if has_whole_content_qa:
        html_content += """
        <div class="whole-content-qa">
            <h2>Key Questions &amp; Answers</h2>
"""
        for qa_pair in qa_pairs.get("whole_content", []):
            question_html = html.escape(qa_pair.get("question", ""))
            answer_html = html.escape(qa_pair.get("answer", "")).replace('\n', '<br>')
            html_content += f"""
            <div class="qa-pair">
                <div class="question">{question_html}</div>
                <div class="answer">{answer_html}</div>
            </div>
"""
        html_content += """
        </div>
"""
        
    html_content += """
        <h2>Summary and Key Topics</h2>
"""
    
    # Add topic sections with transformed content
    for topic in topics:
        topic_html = html.escape(topic)
        html_content += f"""
        <div class="topic-card">
            <h3>{topic_html}</h3>
"""
        
        # Add transformed content
        if topic in transformed_content:
            content_html = html.escape(transformed_content[topic]).replace('\n', '<br>')
            html_content += f"""
            <div class="content-block">
                {content_html}
            </div>
"""
        
        # Add Q&A pairs if we're not using whole content Q&A
        if not has_whole_content_qa and topic in qa_pairs and qa_pairs[topic]:
            html_content += """
            <h4>Questions & Answers</h4>
"""
            for qa_pair in qa_pairs[topic]:
                question_html = html.escape(qa_pair.get("question", ""))
                answer_html = html.escape(qa_pair.get("answer", "")).replace('\n', '<br>')
                html_content += f"""
            <div class="qa-pair">
                <div class="question">{question_html}</div>
                <div class="answer">{answer_html}</div>
            </div>
"""
        
        html_content += """
        </div>
"""
    
    # Close the HTML document
    html_content += f"""
        <footer>
            <p>Generated at {html.escape(metadata.get("summary_generated_at", ""))} • 
            Video ID: {video_id}</p>
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
            "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            "summary_generated_at": "2023-02-20 14:30:00"
        },
        "topics": [
            "Music Video Plot",
            "Song Lyrics",
            "Cultural Impact"
        ],
        "qa_pairs": {
            "whole_content": [
                {
                    "question": "What is the song about?",
                    "answer": "The song is about commitment and never letting someone down."
                },
                {
                    "question": "Why is this song famous on the internet?",
                    "answer": "It became an internet prank called 'Rickrolling' where people are tricked into clicking links to this video."
                }
            ],
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
        "transformed_content": {
            "Music Video Plot": "In this video, a man named Rick is dancing and singing. He moves his arms and legs in a funny way that people like to copy. He sings in different places like a stage and outside.",
            "Song Lyrics": "Rick is singing about being a good friend. He promises to always be there for someone special and never make them sad or tell lies. It's like when you promise to always be nice to your best friend.",
            "Cultural Impact": "This song became super famous because people on the internet started using it as a funny joke. They would trick their friends by saying 'click here for something cool' but the link would take them to this song instead. This joke is called 'Rickrolling'."
        },
        "selected_rubric": {
            "name": "Simple Transformation"
        },
        "audience_level": "general"
    }
    
    html_output = generate_html(test_data)
    
    # Save the HTML to a file for testing
    with open("test_summary.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    
    print("HTML generated and saved to test_summary.html")
