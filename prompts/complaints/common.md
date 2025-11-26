# Common Rules for Complaint Extraction

## What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

## CRITICAL RULES

1. Extract insights ONLY about **Wispr Flow** from the content
2. If a competitor app has issues, do NOT extract those as Wispr Flow complaints
3. If sentiment is not about Wispr Flow, return `null` for sentiment_score
4. Use context clues (subreddit/source, content) to determine if complaints/features are about Wispr

## Complaint Extraction Rules

- **IMPORTANT - Be Specific**: Include specific feature/setting/component names in complaints, not vague references
  - ❌ BAD: "Setting doesn't work"
  - ✅ GOOD: "Smart Formatting doesn't work"
  - ❌ BAD: "Poor device support"
  - ✅ GOOD: "Poor Bluetooth microphone support"

- **CRITICAL - Aggressive Deduplication**: If multiple complaints are about the same CORE ISSUE, combine them into ONE complaint. Look for semantic similarity, not just identical wording.
  - "Forced AI formatting" + "Can't disable AI formatting" = SAME ISSUE → Combine into one: "Cannot disable AI formatting"
  - "App crashes" + "App freezes" + "App disconnects" = SAME ISSUE (stability) → Combine into one: "Frequent crashes and freezes"
  - "Bluetooth doesn't work" + "AirPods not recognized" = SAME ISSUE → Combine into one: "Poor Bluetooth microphone support"
  - "Slow transcription" + "Takes too long to process" = SAME ISSUE → Combine into one: "Slow transcription speed"
  - When combining, choose the quote that best represents the overall issue

- **IMPORTANT - Formatting**:
  - Keep complaint text SHORT (5-10 words max)
  - Use simple, jargon-free language
  - Remove app name (don't say "Wispr Flow")
  - Normalize for clustering (e.g., "Cannot disable AI formatting" not "Forced AI formatting cannot be disabled")
  - Make sure it is clear enough and can be understood if stand alone without additional context
  - Include specific feature/setting names from the content

## Competitor Examples

Common competitors mentioned: Spokenly, Vowen, FluidVoice, VoiceInk, Superwhisper, Talon, Dragon NaturallySpeaking, Siri, Noteflux, Apple Voice to Text

## Sentiment Scoring

- 1 = Very negative about Wispr Flow
- 2 = Somewhat negative about Wispr Flow
- 3 = Neutral about Wispr Flow (has opinion but mixed/balanced)
- 4 = Somewhat positive about Wispr Flow
- 5 = Very positive about Wispr Flow
- **null** = No sentiment expressed OR purely factual/informational content (e.g., questions asking for help, feature announcements, how-to posts, technical discussions without opinion)
- **IMPORTANT**: Only assign a sentiment score if the content expresses an OPINION or FEELING about Wispr Flow. Neutral questions, informational posts, and factual discussions should return null.
