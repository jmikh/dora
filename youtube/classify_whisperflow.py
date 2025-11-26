#!/usr/bin/env python3
"""
Script to classify YouTube videos as related or not related to Whisperflow AI dictation app.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def classify_video(client: OpenAI, title: str, description: str, channel_name: str) -> bool:
    """
    Use OpenAI API to classify if a video is about Wispr Flow AI dictation app.

    Args:
        client: OpenAI client instance
        title: Video title
        description: Video description text or transcript excerpt
        channel_name: YouTube channel name

    Returns:
        True if video is about Whisper flow, False otherwise
    """
    prompt = f"""You are analyzing YouTube videos to determine if they are about Wispr Flow AI, which is an AI-powered voice dictation application.

IMPORTANT DISTINCTIONS:
- Wispr Flow: An AI dictation app that converts speech to text, helps with writing emails, documents, messaging, etc.
- Check for "voice" "dictation" for a good signal
- Channel name can also be a strong signal
- any mention of "wispr flow" or "wisprflow" or "wisper flow ai" means it's a yes.

Only classify as "YES" if the video is specifically about Wispr Flow AI dictation app.

Channel Name: {channel_name}
Video Title: {title}

Video Description/Transcript: {description}

Is this video about Wispr Flow (the AI dictation app)?
Answer with just "YES" or "NO"."""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a precise classifier. Answer only with YES or NO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )

        answer = response.choices[0].message.content.strip().upper()
        return answer == "YES"

    except Exception as e:
        print(f"Error classifying video '{title}': {e}")
        # Default to False on error
        return False


def main():
    """Main function to process YouTube dataset and classify videos."""

    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    client = OpenAI(api_key=api_key)

    # Load dataset
    dataset_path = Path(__file__).parent / 'dataset_youtube_cleaned.json'
    print(f"Loading dataset from: {dataset_path}")

    with open(dataset_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    print(f"Total videos to process: {len(videos)}")

    # Lists to store classified videos
    whisperflow_videos: List[Dict] = []
    not_whisperflow_videos: List[Dict] = []

    # Process each video
    for idx, video in enumerate(videos, 1):
        title = video.get('title', '')
        description = video.get('text', '')
        channel_name = video.get('channelName', '')

        # If description is empty, use up to 200 words from transcript
        if not description or description.strip() == '':
            subtitles = video.get('subtitles', [])
            if subtitles and len(subtitles) > 0:
                transcript = subtitles[0].get('srt', '')
                if transcript:
                    # Get first 200 words from transcript
                    words = transcript.split()
                    description = ' '.join(words[:200])

        print(f"Processing {idx}/{len(videos)}: {title[:60]}...")

        is_whisperflow = classify_video(client, title, description, channel_name)

        if is_whisperflow:
            whisperflow_videos.append(video)
            print(f"  ✓ Classified as WHISPERFLOW")
        else:
            not_whisperflow_videos.append(video)
            print(f"  ✗ Classified as NOT WHISPERFLOW")

    # Save results
    whisperflow_path = Path(__file__).parent / 'actualwhisperflow_youtube.json'
    not_whisperflow_path = Path(__file__).parent / 'notwhisperflow.json'

    print(f"\nSaving {len(whisperflow_videos)} Whisperflow videos to: {whisperflow_path}")
    with open(whisperflow_path, 'w', encoding='utf-8') as f:
        json.dump(whisperflow_videos, f, indent=2, ensure_ascii=False)

    print(f"Saving {len(not_whisperflow_videos)} non-Whisperflow videos to: {not_whisperflow_path}")
    with open(not_whisperflow_path, 'w', encoding='utf-8') as f:
        json.dump(not_whisperflow_videos, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print("CLASSIFICATION SUMMARY")
    print("="*60)
    print(f"Total videos processed: {len(videos)}")
    print(f"Whisperflow videos: {len(whisperflow_videos)}")
    print(f"Not Whisperflow videos: {len(not_whisperflow_videos)}")
    print("="*60)


if __name__ == "__main__":
    main()
