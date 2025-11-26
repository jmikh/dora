# Shared Prompt Components for Wispr Flow Insight Extraction

## What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

---

## Output Schema

Return a JSON object with the following structure:

```json
{
  "competitors_mentioned": ["Competitor1", "Competitor2"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Brief description of complaint",
      "quote": "Exact quote from content"
    }
  ]
}
```

---

## Field Definitions

### competitors_mentioned

List of competitor product names mentioned in the content

**Examples:** Spokenly, Vowen, FluidVoice, VoiceInk, Superwhisper, Talon, Dragon NaturallySpeaking, Siri, Willow Voice, Microsoft Dictation, Noteflux, etc.

**Return:** Empty list if none mentioned

---

### sentiment_score

Integer from 1-5 representing sentiment **about Wispr Flow only**

- **1** = Very negative (angry, frustrated, demanding refund, calling it unusable)
- **2** = Somewhat negative (disappointed, multiple complaints, wouldn't recommend)
- **3** = Neutral (has opinion but mixed/balanced, both pros and cons)
- **4** = Somewhat positive (happy, works well, minor complaints)
- **5** = Very positive (love it, game-changer, highly recommend, enthusiastic)
- **null** = No sentiment expressed OR purely factual/informational content (e.g., support responses, feature explanations, how-to answers, neutral questions)

**IMPORTANT**: Only assign a sentiment score if the content expresses an OPINION or FEELING about Wispr Flow. Factual statements, support answers, informational responses, and neutral questions should return null.

---

### complaints

List of specific problems or complaints **about Wispr Flow**

Each complaint must include:
- **complaint**: Short, normalized complaint text (5-10 words max)
- **quote**: Exact quote from the content

**Extraction Rules:**
- Only extract if clearly about Wispr Flow
- Include both explicit complaints ("X is broken") and implicit ones ("I wish it had Y" → complaint: "Lacks feature Y")
- Each complaint must have a direct quote from the content

**IMPORTANT - Be Specific**: Include specific feature/setting/component names in complaints, not vague references
- ❌ BAD: "Setting doesn't work"
- ✅ GOOD: "Smart Formatting doesn't work"
- ❌ BAD: "Poor device support"
- ✅ GOOD: "Poor Bluetooth microphone support"
- ❌ BAD: "Unclear how to toggle setting"
- ✅ GOOD: "Unclear how to toggle Smart Formatting"

**CRITICAL - Aggressive Deduplication**: If multiple complaints are about the same CORE ISSUE, combine them into ONE complaint. Look for semantic similarity, not just identical wording.

Examples of what should be combined:
- "Forced AI formatting" + "Can't disable AI formatting" = SAME ISSUE → Combine into one: "Cannot disable AI formatting"
- "App crashes" + "App freezes" + "App disconnects" = SAME ISSUE (stability) → Combine into one: "Frequent crashes and freezes"
- "Bluetooth doesn't work" + "AirPods not recognized" = SAME ISSUE → Combine into one: "Poor Bluetooth microphone support"
- "Slow transcription" + "Takes too long to process" = SAME ISSUE → Combine into one: "Slow transcription speed"

When combining, choose the quote that best represents the overall issue.

**IMPORTANT - Formatting Requirements**:
- Keep complaint text SHORT (5-10 words max)
- Use simple, jargon-free language
- Remove app name (don't say "Wispr Flow")
- Normalize for clustering (e.g., "Cannot disable AI formatting" not "Forced AI formatting cannot be disabled")
- Make sure it is clear enough and can be understood standalone without additional context
- Include specific feature/setting names from the content (even if pronouns like "it" or "this" are used)

---

## Core Extraction Rules

1. Only extract insights that are **specifically about Wispr Flow**
2. If a competitor app has issues, do NOT extract those as Wispr Flow complaints
3. If sentiment is not about Wispr Flow, return `null` for sentiment_score
4. Factual statements, support answers, and informational responses = `null` sentiment (no opinion/feeling expressed)
