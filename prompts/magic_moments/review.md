# Magic Moment Extraction Prompt for Wispr Flow

## Your Task

You are extracting **magic moments** from app store reviews for **Wispr Flow**, a voice-to-text dictation app.

You will receive a BATCH of reviews. Your job is to find the **rare, exceptional quotes** that are so powerful they could be featured in marketing campaigns.

## What is a Magic Moment?

A magic moment is a **life-changing revelation** - the user's world has fundamentally shifted. These are the **1 in 100** quotes that make you stop and say "wow, we need to use this."

**TRUE Magic Moments (the bar is THIS high):**
- "This has completely transformed how I work - I'm never going back to typing"
- "I've tried every dictation app for 10 years. Nothing comes close. This is it."
- "My carpal tunnel was ending my career. This app saved my job."
- "I wrote my entire thesis using this. It changed my life."
- "This is what Apple's dictation should have been. Blows it out of the water."
- "I'm 3x more productive. Not exaggerating. Actually 3x."

**NOT Magic Moments (do NOT extract these):**
- "This app is amazing" (generic - anyone says this)
- "I love it" / "I highly recommend it" (standard praise)
- "Best app ever" (overused, not specific)
- "This is incredible" / "This is fantastic" (generic superlatives)
- "Works great" / "So good" (satisfaction, not transformation)
- "Accurate punctuation" / "Picks up my voice well" (feature praise)
- "Helps me write faster" (benefit without emotional weight)
- "Amazing tool" (generic)

## BE EXTREMELY SELECTIVE

- Most batches should return **0-2 magic moments**, not 5+
- If you're unsure, DON'T include it
- Generic enthusiasm is NOT a magic moment
- The quote must be **specific** and **visceral** - you can feel the emotion
- Ask yourself: "Would a marketing team actually use this exact quote?" If not, skip it.

## CRITICAL RULES

1. **VERY FEW quotes qualify** - most reviews have no magic moment
2. Must express genuine **life-changing impact**, not just satisfaction
3. Must be **specific** - generic praise like "amazing app" never qualifies
4. Must be **quotable for marketing** - punchy, compelling, believable
5. Extract the **exact quote** from the review

## Output Schema

Return a JSON object with magic moments found across ALL reviews in the batch:

```json
{
  "magic_moments": [
    {
      "review_id": "abc123",
      "quote": "This has completely transformed how I work"
    },
    {
      "review_id": "def456",
      "quote": "Best app I've ever purchased"
    }
  ]
}
```

If NO magic moments are found in the entire batch, return:

```json
{
  "magic_moments": []
}
```

---

## Example

**REVIEWS BATCH:**

```
Review ID: review_001
Rating: 5 stars
Text: Great app, works well for dictation. I use it for emails. Amazing tool!

Review ID: review_002
Rating: 5 stars
Text: This app is incredible. Best dictation app ever. Highly recommend!

Review ID: review_003
Rating: 5 stars
Text: Good accuracy, helpful for notes. Love the punctuation feature.

Review ID: review_004
Rating: 5 stars
Text: After 15 years of chronic wrist pain from typing, I was about to leave my programming career. This app gave me my job back. I'm not exaggerating - it saved my livelihood.

Review ID: review_005
Rating: 5 stars
Text: Works great! So much faster than typing. I love it.
```

**CORRECT OUTPUT:**

```json
{
  "magic_moments": [
    {
      "review_id": "review_004",
      "quote": "After 15 years of chronic wrist pain from typing, I was about to leave my programming career. This app gave me my job back."
    }
  ]
}
```

**Why only 1 out of 5 reviews:**
- review_001: NO - "Great app", "Amazing tool" is generic praise
- review_002: NO - "incredible", "best ever", "highly recommend" are all generic superlatives
- review_003: NO - feature praise, not emotional impact
- review_004: YES - specific, visceral, life-changing story with real stakes
- review_005: NO - "works great", "love it" is standard satisfaction

---

## Now Extract Magic Moments from These Reviews:

