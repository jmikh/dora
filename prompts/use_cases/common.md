# Common Rules for Use Case Extraction

## What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

## CRITICAL RULES

1. Extract use cases ONLY about **Wispr Flow** from the content
2. If a competitor app use case is mentioned, do NOT extract it as a Wispr Flow use case
3. Use context clues (subreddit/source, content) to determine if use cases are about Wispr Flow
4. Use cases should describe HOW users are using or want to use Wispr Flow

## ❌ NOT Use Cases vs ✅ USE CASES

**CRITICAL**: Wispr's core functionality (dictating, voice typing, smart formatting) is NOT a use case by itself. Use cases must describe **WHAT users are doing** or **WHEN/WHERE they're working**.

### ❌ NOT valid use cases (features or too generic):
- "Dictating" (on its own - that's what the app does)
- "Writing" (too generic - WHAT are they writing?)
- "Typing" (that's what the app does)
- "Transcribing" (that's what the app does)
- "Voice typing" (feature)
- "Smart formatting" (feature)
- "AI transcription" (feature)
- "Hands-free input" (feature)
- "Writing reviews" (meta - just reviewing the app itself)
- "Working on projects" (too vague - WHAT projects?)

### ✅ Valid use cases (activity or context):

**WHAT they're doing (activity-based):**
- "Writing emails"
- "Taking notes"
- "Writing code" or "Vibe coding"
- "Writing PRDs"
- "Talking with ChatGPT"
- "Sending Slack messages"
- "Creating documentation"

**WHEN/WHERE they're working (context-based):**
- "Dictating while driving"
- "Working while walking"
- "Dictating in meetings"
- "Working hands-free"

**Combined (activity + context):**
- "Writing emails while driving"
- "Taking notes in meetings"
- "Coding while walking"

**KEY RULE**: If the use case contains "dictating" or similar feature words, it MUST be paired with either:
- **WHAT**: the specific activity (dictating emails, dictating code, dictating messages)
- **WHEN/WHERE**: the context (dictating while driving, dictating in meetings, dictating while walking)

## Use Case Extraction Rules

- **CRITICAL - Atomic Use Cases**: Extract each use case as a SEPARATE, DISTINCT item. Each use case should stand on its own as a unique way someone uses Wispr Flow.

  **Goal**: Understand different personas and different ways people use Wispr Flow. Each use case = one distinct activity or context.

  **Examples from real reviews:**

  ❌ BAD: Combine multiple use cases into one
  - "Writing notes and emails" → This is TWO distinct use cases

  ✅ GOOD: Separate each use case into its own item
  - "Writing notes"
  - "Writing emails"

  **Real example:**
  Input: "I use it to write notes, write essays with just my voice, and write emails. And also write messages."

  ✅ Correct extraction:
  ```json
  [
    {"use_case": "Writing notes", "quote": "write notes"},
    {"use_case": "Writing essays", "quote": "write essays with just my voice"},
    {"use_case": "Writing emails", "quote": "write emails"},
    {"use_case": "Sending messages", "quote": "write messages"}
  ]
  ```

  **Context-based use cases should also be separated:**
  Input: "I'm always on the go working from my phone. Talk and walk and get work done."

  ✅ Correct extraction:
  ```json
  [
    {"use_case": "Working on mobile", "quote": "working from my phone"},
    {"use_case": "Working while walking", "quote": "talk and walk and get work done"}
  ]
  ```

- **IMPORTANT - Be Specific**: Include specific activities, tools, or contexts
  - ❌ BAD: "Working"
  - ✅ GOOD: "Writing code"
  - ❌ BAD: "Using apps"
  - ✅ GOOD: "Writing in Notion"
  - ❌ BAD: "Communication"
  - ✅ GOOD: "Sending Slack messages"

- **IMPORTANT - Formatting**:
  - Keep use case text SHORT (2-5 words max)
  - Use gerund form (verb + -ing): "Writing emails", "Taking notes", "Coding"
  - Use simple, jargon-free language
  - Remove app name (don't say "Wispr Flow")
  - Make sure it is clear enough and can be understood if stand alone without additional context
  - Focus on the ACTION, not the tool

- **CRITICAL - Only CURRENT, WORKING Use Cases**:
  - ✅ INCLUDE: Use cases the user is ACTUALLY doing successfully
    - "I use it for writing emails" → ✅ Extract
    - "I dictate notes every day" → ✅ Extract
  - ❌ DO NOT INCLUDE:
    - **Hypothetical use cases**: "It would be great for meetings" → ❌ Skip (not actually using it)
    - **Feature requests**: "Add support for coding" → ❌ Skip (doesn't work yet)
    - **Broken/failing use cases**: "I tried using it for coding but it doesn't work" → ❌ Skip (user is upset, not working)
    - **Wishful thinking**: "Would love to use it while driving" → ❌ Skip (not currently doing it)

## Common Use Case Categories

- **Writing**: emails, messages, documentation, notes, content
- **Coding**: writing code, describing code, prompting AI assistants
- **Communication**: messaging, email, chat, social media
- **Productivity**: note-taking, task management, brain dumping
- **Content Creation**: writing articles, documentation, creative writing
- **Contexts**: while driving, in meetings, hands-free, multitasking
