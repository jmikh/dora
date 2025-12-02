# Common Rules for Use Case Extraction

## What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for writing, messaging, coding, and capturing ideas by voice.

## PREDEFINED USE CASE CATEGORIES

You MUST classify each use case into one of these predefined categories:

| Category | Description | Examples |
|----------|-------------|----------|
| `emails` | Writing or composing emails | Gmail, Outlook, Superhuman, work emails, personal emails |
| `messaging` | Texting, chat, instant messaging | Slack, Discord, iMessage, WhatsApp, Teams, SMS, texting |
| `vibe_coding` | Coding with AI assistants, describing code to build software | Cursor, Claude Code, Windsurf, Copilot, using ChatGPT/Claude FOR coding tasks |
| `prompting_llm` | General AI chat for NON-coding tasks | ChatGPT for writing help, Perplexity for research, Gemini for questions, general AI conversations |
| `note_taking` | Taking notes, documentation | Notion, Obsidian, Apple Notes, meeting notes, journaling |
| `brain_dump` | Rambling, synthesizing unstructured ideas, speaking thoughts freely | Stream of consciousness, brainstorming, thinking out loud, capturing raw ideas |
| `on_the_go` | Getting things done while mobile, hands busy | While walking, driving, cooking, commuting, exercising, multitasking |
| `accessibility` | Using due to physical/medical conditions | Carpal tunnel, Parkinson's, arthritis, RSI, speech impediment, disability, injury |
| `improving_english` | ESL users, improving writing/grammar | Non-native speakers, learning English, grammar help, better phrasing |
| `content_creation` | Creating long-form content | Blog posts, articles, documents, social media posts, newsletters, reports |
| `other` | Anything that doesn't fit above categories | Specify what it is |

## CRITICAL RULES

1. Extract use cases ONLY about **Wispr Flow** from the content
2. Each use case MUST map to one of the predefined categories above
3. If it doesn't fit any category, use `other` and specify what it is
4. Only extract **current, working** use cases (not hypotheticals or feature requests)

## Category Selection Guidelines

- **emails** vs **messaging**: Emails are formal/async, messaging is chat/instant
- **vibe_coding** vs **prompting_llm**: Coding uses code-focused AI (Cursor, Windsurf), LLM prompting is general AI chat
- **note_taking** vs **brain_dump**: Notes are structured/organized, brain dump is unstructured rambling
- If someone mentions "writing" without context, look for clues about WHAT they're writing
- If unclear, prefer the more specific category

## What is NOT a Use Case

Do NOT extract these as use cases:
- Generic "dictating" or "voice typing" (that's what the app does)
- Features like "smart formatting" or "AI transcription"
- Hypothetical use cases ("would be great for...")
- Failed/broken use cases ("tried but doesn't work")
- Meta use cases ("writing this review")
