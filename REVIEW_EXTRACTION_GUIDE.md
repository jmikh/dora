# Review Extraction Guide

## Overview

This guide explains how to extract AI insights from app store reviews for Wispr Flow. The system extracts competitor mentions, sentiment scores, and complaints from reviews **without** using the star rating, allowing you to compare AI-inferred sentiment against actual user ratings.

## Key Feature: Rating vs Sentiment Comparison

**Important**: The extraction prompt does NOT receive the star rating. This allows you to:
- Test how well the LLM infers sentiment from text alone
- Identify cases where star rating doesn't match review sentiment
- Find nuanced feedback (e.g., 5-star reviews with complaints)

## Database Schema

### Reviews Table

```sql
reviews (
    review_id TEXT PRIMARY KEY,
    company_id INTEGER,  -- Foreign key to companies
    source TEXT,  -- 'appstore', 'playstore', 'trustpilot', 'producthunt'
    user_name TEXT,
    rating INTEGER,  -- Actual star rating (1-5)
    helpful_votes INTEGER,
    date DATETIME,
    review_text TEXT,
    reply_content TEXT,
    version TEXT,

    -- AI extraction fields
    sentiment_score INTEGER,  -- AI-inferred sentiment (1-5)
    ai_processed BOOLEAN DEFAULT 0
)
```

### Extraction Tables (Shared with Reddit)

```sql
competitor_mentions (
    id INTEGER PRIMARY KEY,
    competitor_name TEXT,
    source_id TEXT,  -- review_id
    source_table TEXT,  -- 'reviews'
    extracted_at TIMESTAMP
)

complaints (
    id INTEGER PRIMARY KEY,
    complaint TEXT,  -- Short, normalized (5-10 words)
    quote TEXT,  -- Exact quote from review
    source_id TEXT,  -- review_id
    source_table TEXT,  -- 'reviews'
    extracted_at TIMESTAMP
)
```

## Files

1. **review_insight_extraction_prompt.md** - LLM prompt with 10 few-shot examples
2. **add_sentiment_score_to_reviews.py** - Migration script
3. **test_review_extraction.py** - Demo script showing workflow
4. **example_ai_extraction.py** - Saves results to database

## Workflow

### 1. Format Review for Extraction

```python
from models import Review, get_session

session = get_session()
review = session.query(Review).filter(Review.review_id == "13111476263").first()

# Format without rating
formatted_review = f"""**REVIEW:**

```
Title: {review.review_text.split('.')[0]}
Author: {review.user_name}
Source: {review.source}
Date: {review.date.strftime('%Y-%m-%d')}

{review.review_text}
```
"""
```

**Note**: We do NOT include `rating` in the prompt!

### 2. Load Prompt and Send to LLM

```python
from pathlib import Path

# Load prompt template
prompt_file = Path("review_insight_extraction_prompt.md")
with open(prompt_file, 'r') as f:
    prompt_template = f.read()

# Replace placeholder with review
full_prompt = prompt_template.replace(
    "[REVIEW WILL BE PROVIDED HERE]",
    formatted_review
)

# Send to LLM (pseudo-code)
ai_response = your_llm.complete(full_prompt)
```

### 3. Expected AI Response

```json
{
  "competitors_mentioned": ["Dragon", "Microsoft Dictation"],
  "sentiment_score": 2,
  "complaints": [
    {
      "complaint": "Significant activation delay",
      "quote": "There is a significant delay between when I tap the hot key..."
    },
    {
      "complaint": "No live preview while dictating",
      "quote": "you can't see what you're typing until you click the button again"
    }
  ]
}
```

### 4. Save to Database

```python
from example_ai_extraction import save_extraction_results

save_extraction_results(
    source_id=review.review_id,
    source_table="reviews",
    ai_response=ai_response
)

# Output:
# ✓ Updated sentiment_score for 13111476263 (actual rating: 1, AI sentiment: 2)
# ✓ Saved 2 competitor mentions
# ✓ Saved 2 complaints
```

### 5. Compare Rating vs Sentiment

```sql
-- Find reviews where AI sentiment differs from rating
SELECT
    review_id,
    rating as actual_rating,
    sentiment_score as ai_sentiment,
    (sentiment_score - rating) as difference,
    user_name,
    LEFT(review_text, 100) as preview
FROM reviews
WHERE
    ai_processed = 1
    AND sentiment_score IS NOT NULL
    AND ABS(sentiment_score - rating) >= 2  -- 2+ star difference
ORDER BY ABS(sentiment_score - rating) DESC;
```

## Sentiment Scale

**1-5 scale (inferred from text, not rating):**

- **1** = Very negative (angry, frustrated, demanding refund, calling it unusable)
- **2** = Somewhat negative (disappointed, multiple complaints, wouldn't recommend)
- **3** = Neutral (mixed feelings, "it's okay", both pros and cons)
- **4** = Somewhat positive (happy, works well, minor complaints)
- **5** = Very positive (love it, game-changer, highly recommend, enthusiastic)

## Complaint Formatting Rules

Complaints must be:
- **Short**: 5-10 words max
- **Jargon-free**: Simple language
- **No app name**: Don't say "Wispr Flow"
- **Normalized**: Ready for clustering
- **Deduplicated**: Combine similar issues into one
- **Clear**: Understandable standalone

**Examples:**
- ✅ "Poor Bluetooth microphone support"
- ✅ "Cannot disable AI formatting"
- ✅ "No customer support response"
- ❌ "Wispr Flow doesn't work with Bluetooth" (has app name)
- ❌ "The Bluetooth connectivity feature is suboptimal" (too wordy, jargon)

## Analytics Queries

### Top Complaints from Reviews

```sql
SELECT
    c.complaint,
    COUNT(*) as mention_count,
    GROUP_CONCAT(DISTINCT r.source) as sources
FROM complaints c
JOIN reviews r ON c.source_id = r.review_id
WHERE c.source_table = 'reviews'
GROUP BY c.complaint
ORDER BY mention_count DESC
LIMIT 20;
```

### Competitor Mentions by Source

```sql
SELECT
    cm.competitor_name,
    r.source,
    COUNT(*) as mentions
FROM competitor_mentions cm
JOIN reviews r ON cm.source_id = r.review_id
WHERE cm.source_table = 'reviews'
GROUP BY cm.competitor_name, r.source
ORDER BY mentions DESC;
```

### Review Processing Status

```sql
SELECT
    source,
    COUNT(*) as total_reviews,
    SUM(CASE WHEN ai_processed = 1 THEN 1 ELSE 0 END) as processed,
    SUM(CASE WHEN ai_processed = 0 THEN 1 ELSE 0 END) as pending,
    ROUND(100.0 * SUM(CASE WHEN ai_processed = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_complete
FROM reviews
GROUP BY source;
```

### Sentiment Accuracy

```sql
-- How often does AI sentiment match actual rating?
SELECT
    CASE
        WHEN sentiment_score = rating THEN 'Exact match'
        WHEN ABS(sentiment_score - rating) = 1 THEN 'Off by 1'
        WHEN ABS(sentiment_score - rating) = 2 THEN 'Off by 2'
        ELSE 'Off by 3+'
    END as accuracy,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM reviews WHERE ai_processed = 1), 1) as percentage
FROM reviews
WHERE ai_processed = 1 AND sentiment_score IS NOT NULL
GROUP BY accuracy
ORDER BY
    CASE accuracy
        WHEN 'Exact match' THEN 1
        WHEN 'Off by 1' THEN 2
        WHEN 'Off by 2' THEN 3
        ELSE 4
    END;
```

## Testing

Run the test script to see the extraction workflow:

```bash
python test_review_extraction.py
```

This will:
1. Load the extraction prompt
2. Format a real review (without rating)
3. Show you the full prompt ready for LLM
4. Demonstrate how to save results

## Example Use Cases

### Use Case 1: Find 5-Star Reviews with Complaints

Even positive reviews may mention issues:

```sql
SELECT
    r.review_id,
    r.rating,
    r.sentiment_score,
    COUNT(c.id) as complaint_count,
    GROUP_CONCAT(c.complaint, '; ') as complaints
FROM reviews r
JOIN complaints c ON c.source_id = r.review_id
WHERE
    r.rating = 5
    AND r.ai_processed = 1
    AND c.source_table = 'reviews'
GROUP BY r.review_id
HAVING complaint_count > 0
ORDER BY complaint_count DESC;
```

### Use Case 2: Find Polarizing Reviews

Reviews where sentiment and rating diverge significantly:

```sql
-- 1-star review but positive text
SELECT * FROM reviews
WHERE rating = 1 AND sentiment_score >= 4;

-- 5-star review but negative text
SELECT * FROM reviews
WHERE rating = 5 AND sentiment_score <= 2;
```

### Use Case 3: Cross-Source Analysis

Compare complaints across Reddit and Reviews:

```sql
SELECT
    complaint,
    SUM(CASE WHEN source_table = 'reviews' THEN 1 ELSE 0 END) as review_mentions,
    SUM(CASE WHEN source_table = 'reddit_content' THEN 1 ELSE 0 END) as reddit_mentions,
    COUNT(*) as total_mentions
FROM complaints
GROUP BY complaint
HAVING total_mentions >= 3
ORDER BY total_mentions DESC;
```

## Notes

- Review extraction uses same `complaints` and `competitor_mentions` tables as Reddit
- The `source_table` field distinguishes between sources
- Sentiment comparison is a powerful way to validate AI accuracy
- Some reviews may have high ratings but contain valuable complaints
- Cross-source analytics help identify common pain points
