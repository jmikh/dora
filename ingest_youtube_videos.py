#!/usr/bin/env python3
"""
Ingest YouTube videos from JSON file into database
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from models import YouTubeVideo, get_session, get_engine, Base


def parse_youtube_date(date_str: str) -> datetime:
    """
    Parse YouTube date string to datetime

    Args:
        date_str: ISO 8601 date string (e.g., "2025-03-12T07:00:02.000Z")

    Returns:
        datetime object
    """
    # Remove 'Z' suffix and milliseconds for parsing
    if date_str.endswith('Z'):
        date_str = date_str[:-1]

    # Handle milliseconds
    if '.' in date_str:
        date_str = date_str.split('.')[0]

    return datetime.fromisoformat(date_str)


def flatten_subtitles(subtitles: Optional[list]) -> tuple:
    """
    Flatten subtitles array to get first subtitle info

    Args:
        subtitles: List of subtitle dictionaries

    Returns:
        Tuple of (subtitle_type, subtitle_language, subtitle_srt)
    """
    if not subtitles or len(subtitles) == 0:
        return None, None, None

    # Take the first subtitle
    subtitle = subtitles[0]
    return (
        subtitle.get('type'),
        subtitle.get('language'),
        subtitle.get('srt')
    )


def ingest_youtube_videos(json_file: Path, company_name: str = 'wispr') -> None:
    """
    Ingest YouTube videos from JSON file into database

    Args:
        json_file: Path to JSON file containing YouTube videos
        company_name: Company name to associate with videos (default: 'wispr')
    """
    print("=" * 80)
    print("INGESTING YOUTUBE VIDEOS")
    print("=" * 80)

    # Create tables if they don't exist
    engine = get_engine()
    Base.metadata.create_all(engine)

    # Load JSON data
    print(f"\n📂 Loading data from {json_file}...")
    with open(json_file, 'r') as f:
        videos_data = json.load(f)

    print(f"   ✅ Loaded {len(videos_data)} videos from JSON")

    # Create database session
    session = get_session()

    # Process each video
    added = 0
    updated = 0
    skipped = 0

    for idx, video_data in enumerate(videos_data, 1):
        video_id = video_data.get('id')

        if not video_id:
            print(f"[{idx}/{len(videos_data)}] ⚠️  Skipping video without ID")
            skipped += 1
            continue

        # Check if video already exists
        existing_video = session.query(YouTubeVideo).filter(
            YouTubeVideo.id == video_id
        ).first()

        # Parse date
        date_str = video_data.get('date')
        if date_str:
            try:
                video_date = parse_youtube_date(date_str)
            except Exception as e:
                print(f"[{idx}/{len(videos_data)}] ⚠️  Error parsing date for {video_id}: {e}")
                video_date = None
        else:
            video_date = None

        # Flatten subtitles
        subtitle_type, subtitle_lang, subtitle_srt = flatten_subtitles(
            video_data.get('subtitles')
        )

        # Flatten hashtags to JSON string
        hashtags = video_data.get('hashtags')
        hashtags_str = json.dumps(hashtags) if hashtags else None

        if existing_video:
            # Update existing video
            existing_video.title = video_data.get('title', existing_video.title)
            existing_video.translated_title = video_data.get('translatedTitle')
            existing_video.type = video_data.get('type')
            existing_video.url = video_data.get('url', existing_video.url)
            existing_video.thumbnail_url = video_data.get('thumbnailUrl')
            existing_video.view_count = video_data.get('viewCount', 0)
            existing_video.likes = video_data.get('likes', 0)
            existing_video.comments_count = video_data.get('commentsCount', 0)
            existing_video.date = video_date or existing_video.date
            existing_video.channel_name = video_data.get('channelName')
            existing_video.channel_url = video_data.get('channelUrl')
            existing_video.channel_username = video_data.get('channelUsername')
            existing_video.channel_id = video_data.get('channelId')
            existing_video.number_of_subscribers = video_data.get('numberOfSubscribers', 0)
            existing_video.duration = video_data.get('duration')
            existing_video.text = video_data.get('text')
            existing_video.translated_text = video_data.get('translatedText')
            existing_video.subtitle_type = subtitle_type
            existing_video.subtitle_language = subtitle_lang
            existing_video.subtitle_srt = subtitle_srt
            existing_video.location = video_data.get('location')
            existing_video.collaborators = video_data.get('collaborators')
            existing_video.order = video_data.get('order')
            existing_video.comments_turned_off = video_data.get('commentsTurnedOff', False)
            existing_video.from_yt_url = video_data.get('fromYTUrl')
            existing_video.is_monetized = video_data.get('isMonetized')
            existing_video.hashtags = hashtags_str
            existing_video.is_members_only = video_data.get('isMembersOnly', False)
            existing_video.input_query = video_data.get('input')

            updated += 1
            action = "Updated"
        else:
            # Create new video
            video = YouTubeVideo(
                id=video_id,
                company_name=company_name,
                title=video_data.get('title', ''),
                translated_title=video_data.get('translatedTitle'),
                type=video_data.get('type'),
                url=video_data.get('url', ''),
                thumbnail_url=video_data.get('thumbnailUrl'),
                view_count=video_data.get('viewCount', 0),
                likes=video_data.get('likes', 0),
                comments_count=video_data.get('commentsCount', 0),
                date=video_date,
                channel_name=video_data.get('channelName'),
                channel_url=video_data.get('channelUrl'),
                channel_username=video_data.get('channelUsername'),
                channel_id=video_data.get('channelId'),
                number_of_subscribers=video_data.get('numberOfSubscribers', 0),
                duration=video_data.get('duration'),
                text=video_data.get('text'),
                translated_text=video_data.get('translatedText'),
                subtitle_type=subtitle_type,
                subtitle_language=subtitle_lang,
                subtitle_srt=subtitle_srt,
                location=video_data.get('location'),
                collaborators=video_data.get('collaborators'),
                order=video_data.get('order'),
                comments_turned_off=video_data.get('commentsTurnedOff', False),
                from_yt_url=video_data.get('fromYTUrl'),
                is_monetized=video_data.get('isMonetized'),
                hashtags=hashtags_str,
                is_members_only=video_data.get('isMembersOnly', False),
                input_query=video_data.get('input')
            )
            session.add(video)
            added += 1
            action = "Added"

        title_preview = video_data.get('title', 'No title')[:50]
        print(f"[{idx}/{len(videos_data)}] {action} video: {video_id} - {title_preview}...")

    # Commit all changes
    session.commit()
    session.close()

    # Summary
    print("\n" + "=" * 80)
    print("✅ INGESTION COMPLETE")
    print("=" * 80)
    print(f"Videos added: {added}")
    print(f"Videos updated: {updated}")
    print(f"Videos skipped: {skipped}")
    print(f"Total processed: {added + updated + skipped}")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest YouTube videos from JSON")
    parser.add_argument(
        "--file",
        type=str,
        default="youtube/actualwhisperflow_youtube.json",
        help="Path to JSON file with YouTube videos"
    )
    parser.add_argument(
        "--company",
        type=str,
        default="wispr",
        help="Company name to associate with videos (default: wispr)"
    )

    args = parser.parse_args()

    json_file = Path(args.file)

    if not json_file.exists():
        print(f"❌ Error: File not found: {json_file}")
        exit(1)

    ingest_youtube_videos(json_file, company_name=args.company)
