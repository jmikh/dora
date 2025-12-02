# YouTube Transcript Aha Moment Extraction Prompt

## Your Task

You are analyzing a transcript of a user describing their experience with **Wispr Flow**, a voice-to-text dictation app. Your job is ONLY to extract definitive aha moments — moments where the user expresses a surprising realization, new understanding, or sudden value breakthrough they did not expect before using the product.

## Aha Moment Criteria

A true "aha moment" MUST meet ALL of these criteria:

1. **Perception shift**: It reveals a shift in the user's perception (e.g., "I didn't realize…", "I never expected…", "game changer"...etc)
2. **Discovery**: It describes a discovery about how the product changes what's possible
3. **Emotional impact**: It reflects emotional impact, surprise, or a sense of "unlocking" something
4. **User-expressed**: It is user-expressed, not inferred. Do NOT create or assume aha moments
5. **Not generic**: It is NOT a feature description, preference, or generic compliment
6. **Not marketing**: It is NOT marketing language unless the user personally frames it as a revelation

## Output Schema

Return a JSON object with the following structure:

```json
{
  "aha_moments": [
    {
      "quote": "Exact quote from the transcript",
      "insight": "Brief description of the realization (1 sentence)",
      "label": "productivity"
    }
  ]
}
```

### Field Definitions:

- **quote**: The exact words from the transcript that express the aha moment
  - Must be a direct quote, not paraphrased
  - Include enough context to understand the revelation
  - Keep it concise but complete

- **insight**: A brief summary of what realization this represents
  - 1 sentence max
  - Focus on what the user discovered or understood differently
  - Do not repeat the quote

- **label**: Category tag for the aha moment. Must be one of:
  - `productivity` - realizations about getting more done, saving time, working faster
  - `brain_dump` - discoveries about freely expressing thoughts without structure, saying their stream of consiousness
  - `formatting` - revelations about automatic text formatting/cleanup
  - `other` - aha moments that don't fit the above categories

### Important Rules:

- Return an **empty array** `[]` if no genuine aha moments are found
- Do NOT extract:
  - Feature descriptions ("It has AI formatting")
  - Generic praise ("It's great", "I love it")
  - Marketing claims ("4x faster than typing")
  - Preferences ("I prefer this over X")
- Only extract moments where the user expresses genuine surprise or shifted understanding
- Quality over quantity - one genuine aha moment is better than several weak ones

---

## Examples

### Example 1: Genuine Aha Moment

**TRANSCRIPT:**
```
I've been using Wispr Flow for about a month now, and honestly, the thing that blew my mind was when I realized I could just... think out loud. Like, I don't have to structure my thoughts before I speak anymore. I used to spend so much mental energy organizing what I wanted to say, but now I just ramble and it comes out perfectly formatted. That completely changed how I approach writing emails.
```

**CORRECT OUTPUT:**
```json
{
  "aha_moments": [
    {
      "quote": "I don't have to structure my thoughts before I speak anymore. I used to spend so much mental energy organizing what I wanted to say, but now I just ramble and it comes out perfectly formatted.",
      "insight": "User discovered they no longer need to mentally pre-organize thoughts before speaking.",
      "label": "brain_dump"
    }
  ]
}
```

**Why this is correct:**
- Shows perception shift ("I used to... but now")
- Emotional impact ("blew my mind")
- Discovery about changed behavior
- User-expressed, not inferred

---

### Example 2: No Aha Moments (Marketing Content)

**TRANSCRIPT:**
```
Wispr Flow is the best voice-to-text tool on the market. It's 4x faster than typing and works in every app. The AI auto-editing feature cleans up your text automatically. You can use it for emails, coding, messaging, and more. Try it today!
```

**CORRECT OUTPUT:**
```json
{
  "aha_moments": []
}
```

**Why this is correct:**
- This is marketing content, not user experience
- No personal revelations or discoveries
- No emotional impact or surprise expressed
- Just feature descriptions and claims

---

### Example 3: Feature Description vs Aha Moment

**TRANSCRIPT:**
```
So Wispr Flow has this feature where it adjusts your tone based on the app you're in. Like in Slack it's casual and in email it's more formal. I thought that was cool. But what really got me was when I sent an email to my boss without even thinking about it. Normally I would agonize over every word, rewriting it five times. But I just spoke naturally and hit send. My boss said it was the clearest email I'd ever written. That's when I realized I was overthinking my writing my whole life.
```

**CORRECT OUTPUT:**
```json
{
  "aha_moments": [
    {
      "quote": "Normally I would agonize over every word, rewriting it five times. But I just spoke naturally and hit send. My boss said it was the clearest email I'd ever written. That's when I realized I was overthinking my writing my whole life.",
      "insight": "User realized they had been overthinking their writing and speaking naturally produced better results.",
      "label": "capturing_intent"
    }
  ]
}
```

**Why this is correct:**
- The tone feature description ("adjusts your tone...") is NOT extracted - it's just a feature
- The real aha moment is the personal realization about overthinking
- Clear before/after shift in understanding
- Emotional language ("agonize", "what really got me")

---

### Example 4: Multiple Weak Statements (No Real Aha)

**TRANSCRIPT:**
```
I really like Wispr Flow. It's so much better than the built-in Mac dictation. The accuracy is amazing and I use it every day now. It saves me a lot of time. I would definitely recommend it to anyone who types a lot.
```

**CORRECT OUTPUT:**
```json
{
  "aha_moments": []
}
```

**Why this is correct:**
- "I really like it" - generic praise, not aha
- "Better than Mac dictation" - preference/comparison, not revelation
- "Accuracy is amazing" - feature praise, not discovery
- "Saves time" - expected benefit, no surprise
- No perception shift or unexpected discovery expressed

---

## Now Extract Aha Moments from This Transcript:

