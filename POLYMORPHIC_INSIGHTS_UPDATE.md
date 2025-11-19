# Polymorphic Insights Update

## Overview
Updated the insights system to support extracting insights from both **reviews** and **YouTube videos** as sources. This allows the system to analyze user feedback from multiple content types while maintaining a unified insights database.

## Changes Made

### 1. Database Schema Updates

#### Insight Table - Added Polymorphic Source Fields
```sql
ALTER TABLE insights ADD COLUMN source_type TEXT NOT NULL DEFAULT 'review';
ALTER TABLE insights ADD COLUMN source_id TEXT NOT NULL;
```

**New fields:**
- `source_type`: 'review' or 'youtube_video'
- `source_id`: ID of the source (review_id or video_id)
- `review_id`: Made nullable for backward compatibility

**Migration:** `add_polymorphic_source.py`
- Migrated 1,976 existing insights
- Set source_type='review' and source_id=review_id for all existing insights

#### YouTubeVideo Table - Added Company Association
```sql
ALTER TABLE youtube_videos ADD COLUMN company_name TEXT NOT NULL DEFAULT 'wispr';
```

**Migration:** `add_company_name_to_youtube.py`
- Added company_name column
- Set company_name='wispr' for all 65 existing videos

### 2. Model Updates (models.py)

#### Updated Insight Model
```python
class Insight(Base):
    # ...existing fields...

    # Polymorphic source fields
    source_type = Column(Text, nullable=False, default='review')
    source_id = Column(Text, nullable=False)

    # review_id now nullable for backward compatibility
    review_id = Column(Text, ForeignKey("reviews.review_id"), nullable=True)
```

#### Updated YouTubeVideo Model
```python
class YouTubeVideo(Base):
    id = Column(String, primary_key=True, nullable=False)
    company_name = Column(Text, nullable=False, default='wispr')  # NEW
    title = Column(Text, nullable=False)
    # ...rest of fields...
```

### 3. Insight Extraction Updates (extract_insights.py)

#### New Functions for YouTube Videos

**get_youtube_videos_to_process()**
- Fetches YouTube videos with subtitles or descriptions
- Ordered by view count (most popular first)

**extract_insights_from_youtube_video()**
- Combines video title, description, and transcript (from SRT)
- Parses SRT to extract clean text (removes timestamps)
- Uses same OpenAI extraction as reviews

**store_youtube_insights()**
- Stores insights with source_type='youtube_video'
- Uses video.id as source_id
- Uses video upload date as review_date

**process_youtube_videos()**
- Main function to process YouTube videos
- Similar flow to process_reviews()

#### Updated CLI Arguments
```bash
# Extract insights from reviews (default)
python extract_insights.py --company wispr --limit 10

# Extract insights from YouTube videos
python extract_insights.py --company wispr --source youtube --limit 5

# Specify prompt version
python extract_insights.py --company wispr --source youtube --prompt-version 3
```

**New arguments:**
- `--source`: Choose 'reviews' or 'youtube' (default: reviews)
- `--prompt-version`: Default changed to 3 (use_cases support)

### 4. Ingestion Updates (ingest_youtube_videos.py)

**Updated function signature:**
```python
def ingest_youtube_videos(json_file: Path, company_name: str = 'wispr') -> None:
```

**New CLI argument:**
```bash
python ingest_youtube_videos.py --file youtube/data.json --company wispr
```

### 5. Database Consolidation

**Completed earlier:**
- Merged youtube_videos.db into main noom_playstore_reviews.db
- Deleted separate youtube_videos.db and youtube_models.py
- Updated all scripts to use single database

## Usage Examples

### Extract Insights from YouTube Videos

```bash
# Process all YouTube videos
python extract_insights.py --company wispr --source youtube --prompt-version 3

# Process top 10 most viewed videos
python extract_insights.py --company wispr --source youtube --limit 10

# Process specific number of videos
python extract_insights.py --company wispr --source youtube --limit 5
```

### Query Insights by Source

```sql
-- Count insights by source type
SELECT source_type, insight_type, COUNT(*) as count
FROM insights
GROUP BY source_type, insight_type;

-- Results:
-- review|feature_request|79
-- review|pain_point|942
-- review|praise|808
-- review|use_case|147
-- youtube_video|feature_request|2
-- youtube_video|pain_point|2
-- youtube_video|use_case|4

-- Get YouTube video insights with video details
SELECT
    i.insight_text,
    i.insight_type,
    v.title as video_title,
    v.view_count,
    v.url
FROM insights i
JOIN youtube_videos v ON i.source_id = v.id
WHERE i.source_type = 'youtube_video'
ORDER BY v.view_count DESC;
```

### Python Queries

```python
from models import Insight, Review, YouTubeVideo, get_session

session = get_session()

# Get all YouTube video insights
youtube_insights = session.query(Insight).filter(
    Insight.source_type == 'youtube_video'
).all()

# Get insights with source details (polymorphic)
insights = session.query(Insight).all()
for insight in insights:
    if insight.source_type == 'review':
        review = session.query(Review).filter(
            Review.review_id == insight.source_id
        ).first()
        print(f"Review: {review.review_text[:50]}...")
    else:  # youtube_video
        video = session.query(YouTubeVideo).filter(
            YouTubeVideo.id == insight.source_id
        ).first()
        print(f"Video: {video.title} ({video.view_count:,} views)")
```

## Data Statistics

### Current Insights Breakdown
- **Total Insights:** 1,984
  - From reviews: 1,976 (79 feature requests, 942 pain points, 808 praise, 147 use cases)
  - From YouTube: 8 (2 feature requests, 2 pain points, 4 use cases)

### YouTube Video Content
- **Total Videos:** 65 (all third-party, Wispr Flow AI channel excluded)
- **Videos with subtitles/descriptions:** ~65 (eligible for extraction)
- **Total Views:** 1,199,236
- **Total Likes:** 7,483

## Testing Results

### Test 1: Single Video Extraction
```bash
python extract_insights.py --company wispr --source youtube --limit 1
```

**Results:**
- Video: "This AI app has TRIPLED my Productivity" (120,183 views)
- Extracted: 8 insights (2 pain points, 2 feature requests, 4 use cases)
- Average: 8 insights per video

**Sample Insights:**
- **Pain:** "losing focus on text box while dictating"
- **Feature:** "integrate voice dictation into Windows with formatting"
- **Use Case:** "writing emails in Outlook"

## Files Created/Modified

### New Files
1. `add_polymorphic_source.py` - Migration script for insights table
2. `add_company_name_to_youtube.py` - Migration script for youtube_videos table
3. `POLYMORPHIC_INSIGHTS_UPDATE.md` - This documentation

### Modified Files
1. `models.py` - Updated Insight and YouTubeVideo models
2. `extract_insights.py` - Added YouTube video support
3. `ingest_youtube_videos.py` - Added company_name parameter
4. `generate_dashboard_data.py` - Updated to use consolidated database

## Architecture Benefits

### Extensibility
- Easy to add new source types (e.g., 'twitter_post', 'reddit_comment')
- Just add new source_type value and create extraction function

### Data Integrity
- source_type + source_id provides clear traceability
- No ambiguity about insight origin
- Backward compatible with existing review-based insights

### Query Flexibility
- Can filter insights by source type
- Can join with source tables for context
- Supports aggregations across sources or per-source

## Next Steps

### Potential Enhancements
1. **Batch Process All Videos:**
   ```bash
   python extract_insights.py --company wispr --source youtube
   ```

2. **Generate Embeddings for YouTube Insights:**
   ```bash
   python generate_embeddings.py --company wispr
   ```

3. **Cluster YouTube Insights:**
   ```bash
   python cluster_insights.py --company wispr
   ```

4. **Update Dashboard:**
   - Show source breakdown in pain points timeline
   - Add YouTube-specific insights visualization
   - Display video thumbnails with insights

5. **Cross-Source Analysis:**
   - Compare pain points from reviews vs. YouTube
   - Identify common themes across sources
   - Weighted insights by view count/rating

## Summary

✅ Added polymorphic source support to Insight model
✅ Migrated 1,976 existing insights with source_type='review'
✅ Added company_name to youtube_videos table (65 videos)
✅ Implemented YouTube video insight extraction
✅ Tested successfully with real video data (8 insights extracted)
✅ Updated CLI with --source argument for easy switching
✅ Maintained backward compatibility with existing code

The system can now extract insights from both reviews and YouTube videos, providing a more comprehensive view of user feedback and product discussions!
