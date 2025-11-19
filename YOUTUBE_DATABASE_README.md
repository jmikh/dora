# YouTube Videos Database

## Overview
Created a new SQLite database (`youtube_videos.db`) to store YouTube video data for Wispr Flow. The database contains 78 videos with complete metadata, metrics, and subtitles.

## Database Details

**Database File:** `youtube_videos.db`
**Table:** `youtube_videos`
**Total Videos:** 78

## Schema

### YouTubeVideo Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | String (PK) | YouTube video ID |
| `title` | Text | Video title |
| `translated_title` | Text | Translated title (if available) |
| `type` | String | Video type ('video', 'short', etc.) |
| `url` | Text | Full YouTube URL |
| `thumbnail_url` | Text | Thumbnail image URL |
| `view_count` | Integer | Number of views |
| `likes` | Integer | Number of likes |
| `comments_count` | Integer | Number of comments |
| `date` | DateTime | Upload/publish date |
| `channel_name` | Text | Channel name |
| `channel_url` | Text | Channel URL |
| `channel_username` | Text | Channel username |
| `channel_id` | String | YouTube channel ID |
| `number_of_subscribers` | Integer | Channel subscriber count |
| `duration` | String | Video duration (format: "00:01:26") |
| `text` | Text | Video description text |
| `translated_text` | Text | Translated description (if available) |
| `subtitle_type` | String | Subtitle type ('auto_generated' or 'manual') |
| `subtitle_language` | String | Subtitle language code |
| `subtitle_srt` | Text | Full SRT subtitle content |
| `location` | Text | Video location (if specified) |
| `collaborators` | Text | Video collaborators (if any) |
| `order` | Integer | Video order in dataset |
| `comments_turned_off` | Boolean | Whether comments are disabled |
| `from_yt_url` | Text | Source YouTube search URL |
| `is_monetized` | Boolean | Monetization status |
| `hashtags` | Text | JSON array of hashtags |
| `is_members_only` | Boolean | Members-only status |
| `input_query` | Text | Search query used to find video |

## Data Flattening

The following nested fields were flattened:

1. **Subtitles**: Extracted first subtitle from `subtitles[]` array into:
   - `subtitle_type`
   - `subtitle_language`
   - `subtitle_srt`

2. **Hashtags**: Converted from array to JSON string
   - Stored as: `["#AI", "#Productivity", "#tech"]`

3. **descriptionLinks**: Excluded (not imported as requested)

## Video Statistics

### By Channel (Top 10)

| Channel | Videos | Total Views | Total Likes |
|---------|--------|-------------|-------------|
| Wispr Flow AI | 13 | 797,089 | 834 |
| Savage Reviews | 3 | 10,607 | 0 |
| A Fading Thought | 2 | 31,879 | 815 |
| AsapGuide | 2 | 3,590 | 42 |
| Drex Solan | 2 | 496 | 4 |
| EasyTutoFlow | 2 | 161 | 2 |
| Boldacious Digital | 2 | 32 | 1 |
| Vapi | 1 | 81 | 2 |
| And 45+ other channels | 1 each | - | - |

### Content Coverage

- **With subtitles**: Most videos have auto-generated English subtitles
- **Average subtitle length**: ~1,000+ characters of SRT content
- **Date range**: Videos from 2025 (recent uploads)

## Files Created

1. **youtube_models.py** - SQLAlchemy models for YouTube videos
   - `YouTubeVideo` model with all fields
   - `get_session()` - Create database session
   - `create_tables()` - Initialize database schema

2. **ingest_youtube_videos.py** - Data ingestion script
   - Loads JSON data
   - Flattens nested fields
   - Handles date parsing
   - Supports updates for existing videos
   - Usage: `python ingest_youtube_videos.py --file youtube/actualwhisperflow_youtube.json`

3. **youtube_videos.db** - SQLite database (78 videos)

## Usage Examples

### Query videos from database:

```python
from youtube_models import get_session, YouTubeVideo

session = get_session()

# Get all videos by Wispr Flow AI channel
videos = session.query(YouTubeVideo).filter(
    YouTubeVideo.channel_name == "Wispr Flow AI"
).all()

# Get top 10 most viewed videos
top_videos = session.query(YouTubeVideo).order_by(
    YouTubeVideo.view_count.desc()
).limit(10).all()

# Get videos with subtitles
videos_with_subs = session.query(YouTubeVideo).filter(
    YouTubeVideo.subtitle_srt.isnot(None)
).all()

session.close()
```

### SQL Queries:

```sql
-- Get total stats by channel
SELECT
    channel_name,
    COUNT(*) as video_count,
    SUM(view_count) as total_views,
    AVG(view_count) as avg_views,
    SUM(likes) as total_likes
FROM youtube_videos
GROUP BY channel_name
ORDER BY total_views DESC;

-- Find videos with most engagement
SELECT
    title,
    view_count,
    likes,
    comments_count,
    (likes * 1.0 / NULLIF(view_count, 0)) * 100 as like_rate
FROM youtube_videos
ORDER BY like_rate DESC
LIMIT 10;

-- Get videos published in specific date range
SELECT title, date, view_count
FROM youtube_videos
WHERE date BETWEEN '2025-03-01' AND '2025-04-01'
ORDER BY date DESC;
```

## Re-ingesting Data

To update the database with new video data:

```bash
python ingest_youtube_videos.py --file youtube/actualwhisperflow_youtube.json
```

The script will:
- Add new videos
- Update existing videos (matched by video ID)
- Report summary of changes

## Next Steps

Possible enhancements:
1. Extract insights from video descriptions and subtitles
2. Sentiment analysis on subtitles
3. Track video performance over time
4. Generate reports on content themes
5. Compare metrics across channels
6. Extract keywords/topics from subtitles

## Summary

✅ Created `youtube_videos.db` database
✅ Defined schema with 28 fields
✅ Ingested 78 YouTube videos
✅ Flattened nested fields (subtitles, hashtags)
✅ Excluded descriptionLinks as requested
✅ All data verified and queryable
