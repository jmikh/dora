# Magic Moment Extraction Prompt for Wispr Flow - Reddit

## Your Task

You are extracting **magic moments** from Reddit posts/comments about **Wispr Flow**, a voice-to-text dictation app.

You will receive a BATCH of Reddit content. Your job is to find the **rare, exceptional quotes** that are so powerful they could be featured in marketing campaigns.

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
- "Game changer" without specific context (overused)

## BE EXTREMELY SELECTIVE

- Most batches should return **0-2 magic moments**, not 5+
- If you're unsure, DON'T include it
- Generic enthusiasm is NOT a magic moment
- The quote must be **specific** and **visceral** - you can feel the emotion
- Ask yourself: "Would a marketing team actually use this exact quote?" If not, skip it.

## CRITICAL RULES

1. **VERY FEW quotes qualify** - most posts have no magic moment
2. Must express genuine **life-changing impact**, not just satisfaction
3. Must be **specific** - generic praise like "amazing app" never qualifies
4. Must be **quotable for marketing** - punchy, compelling, believable
5. Extract the **exact quote** from the content

## Output Schema

Return a JSON object with magic moments found across ALL content in the batch:

```json
{
  "magic_moments": [
    {
      "content_id": "t3_abc123",
      "quote": "Exact quote from the post/comment"
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

**REDDIT BATCH:**

```
Content ID: t3_post001
Type: post
Title: Wispr Flow is great
Body: Just started using Wispr Flow. This app is amazing! Highly recommend it to everyone.

Content ID: t1_comment002
Type: comment
Body: Love this app. Works so well for emails and messages. Best dictation app I've tried.

Content ID: t3_post003
Type: post
Title: Wispr gave me my career back
Body: I'm a writer who developed severe RSI two years ago. I thought my career was over. I couldn't type more than 10 minutes without excruciating pain. Wispr Flow has literally given me my livelihood back. I just wrote a 50,000 word novel using only my voice. I'm crying as I write this.

Content ID: t1_comment004
Type: comment
Body: Super accurate, works in all my apps. Really good stuff.
```

**CORRECT OUTPUT:**

```json
{
  "magic_moments": [
    {
      "content_id": "t3_post003",
      "quote": "Wispr Flow has literally given me my livelihood back. I just wrote a 50,000 word novel using only my voice."
    }
  ]
}
```

**Why only 1 out of 4:**
- post001: NO - "amazing", "highly recommend" is generic praise
- comment002: NO - "love this app", "best I've tried" is standard satisfaction
- post003: YES - specific life story, visceral emotion, concrete achievement (50k novel)
- comment004: NO - feature praise, no emotional weight

---

## Now Extract Magic Moments from This Reddit Content:

