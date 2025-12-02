#!/usr/bin/env python3
"""
Extract Aha Moments from YouTube Video Subtitles

Extract aha moment quotes from YouTube video subtitles using OpenAI LLM.

Usage:
    # Extract from a specific video by ID
    python extract_aha_moments.py --id G9jVVM285_w

    # Extract from all unprocessed videos
    python extract_aha_moments.py --limit 5

    # Verbose output
    python extract_aha_moments.py --id G9jVVM285_w --verbose
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Database path
DB_FILE = Path(__file__).parent / "dora.db"


def load_prompt() -> str:
    """Load the aha moments prompt template"""
    prompt_path = Path(__file__).parent / "prompts" / "aha_moments" / "youtube.md"
    with open(prompt_path, 'r') as f:
        return f.read()


def call_llm(prompt: str, client: OpenAI, model: str = "gpt-5-mini") -> Dict:
    """
    Call OpenAI API to extract aha moments

    Args:
        prompt: The complete prompt to send
        client: OpenAI client instance
        model: Model to use

    Returns:
        Parsed JSON response from LLM
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"}
    )

    result_text = response.choices[0].message.content
    return json.loads(result_text)


def save_aha_moments(video_id: str, aha_moments: List[Dict]) -> int:
    """
    Save aha moments to database and mark video as processed

    Args:
        video_id: YouTube video ID
        aha_moments: List of aha moment dicts with "quote" and "insight" keys

    Returns:
        Number of aha moments saved
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Remove existing aha moments for this video
        cursor.execute(
            "DELETE FROM aha_moments WHERE video_id = ?",
            (video_id,)
        )

        # Add new aha moments
        for moment in aha_moments:
            cursor.execute(
                """
                INSERT INTO aha_moments (video_id, quote, insight, label)
                VALUES (?, ?, ?, ?)
                """,
                (video_id, moment["quote"], moment["insight"], moment.get("label", "other"))
            )

        # Mark video as processed
        cursor.execute(
            "UPDATE youtube_videos SET aha_processed = 1 WHERE id = ?",
            (video_id,)
        )

        conn.commit()
        return len(aha_moments)

    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_video_by_id(video_id: str) -> Optional[Dict]:
    """Get a single video by ID"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, subtitle_srt, aha_processed
        FROM youtube_videos
        WHERE id = ?
        """,
        (video_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_unprocessed_videos(limit: Optional[int] = None) -> List[Dict]:
    """Get videos that haven't been processed for aha moments"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT id, title, subtitle_srt
        FROM youtube_videos
        WHERE subtitle_srt IS NOT NULL
          AND length(subtitle_srt) > 0
          AND view_count > 500
          AND (aha_processed = 0 OR aha_processed IS NULL)
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def extract_from_video(
    video: Dict,
    client: OpenAI,
    base_prompt: str,
    verbose: bool = False
) -> int:
    """
    Extract aha moments from a single video

    Args:
        video: Video dict with id, title, subtitle_srt
        client: OpenAI client
        base_prompt: The prompt template
        verbose: Print detailed output

    Returns:
        Number of aha moments extracted
    """
    video_id = video["id"]
    title = video["title"]
    subtitle_srt = video["subtitle_srt"]

    print(f"\n{'='*80}")
    print(f"Processing: {title}")
    print(f"ID: {video_id}")
    print(f"Subtitle length: {len(subtitle_srt)} chars")
    print("="*80)

    # Build the full prompt
    full_prompt = base_prompt + f"\n```\n{subtitle_srt}\n```"

    # Call LLM
    print("\nCalling LLM...")
    ai_response = call_llm(full_prompt, client, model="gpt-5")

    aha_moments = ai_response.get("aha_moments", [])

    # Save results
    num_saved = save_aha_moments(video_id, aha_moments)

    # Print results
    print(f"\nExtracted Aha Moments ({num_saved}):")
    if aha_moments:
        for i, moment in enumerate(aha_moments, 1):
            label = moment.get('label', 'other')
            print(f"\n  {i}. [{label}] Quote: \"{moment['quote'][:150]}{'...' if len(moment['quote']) > 150 else ''}\"")
            print(f"     Insight: {moment['insight']}")
    else:
        print("  (none found)")

    if verbose:
        print("\nFull LLM Response:")
        print(json.dumps(ai_response, indent=2))

    return num_saved


def main():
    parser = argparse.ArgumentParser(
        description="Extract aha moments from YouTube video subtitles"
    )

    parser.add_argument(
        "--id",
        type=str,
        help="Specific video ID to process"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of videos to process (ignored if --id is specified)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    print("="*80)
    print("AHA MOMENT EXTRACTION")
    print("="*80)

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment")
        return

    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized")

    # Load prompt
    base_prompt = load_prompt()
    print("Prompt loaded")

    # Get videos to process
    if args.id:
        video = get_video_by_id(args.id)
        if not video:
            print(f"\nError: Video with ID '{args.id}' not found")
            return

        if not video.get("subtitle_srt"):
            print(f"\nError: Video '{args.id}' has no subtitle_srt data")
            return

        videos = [video]
        print(f"\nProcessing specific video: {args.id}")
    else:
        videos = get_unprocessed_videos(args.limit)
        print(f"\nFound {len(videos)} unprocessed videos")

    if not videos:
        print("No videos to process")
        return

    # Process videos
    total_moments = 0
    for video in videos:
        try:
            count = extract_from_video(video, client, base_prompt, args.verbose)
            total_moments += count
        except Exception as e:
            print(f"\nError processing video {video['id']}: {e}")
            if args.verbose:
                raise

    print(f"\n{'='*80}")
    print(f"COMPLETE: Processed {len(videos)} videos, extracted {total_moments} aha moments")
    print("="*80)


if __name__ == "__main__":
    main()
