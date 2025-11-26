# Use Case Classification Prompt for Wispr Flow

## About Wispr Flow

Wispr Flow is a voice dictation app that allows users to convert speech to text across various applications. Users commonly use it for:
- Writing emails (Gmail, Outlook, Superhuman)
- Messaging (Slack, Discord, iMessage, WhatsApp, Teams)
- AI prompting (ChatGPT, Claude, Cursor, Windsurf)
- Coding assistance ("vibe coding" - describing code to AI assistants)
- Note-taking (Notion, Obsidian, Apple Notes, brain dumping ideas)
- Documentation (writing docs, creating content)

## Your Task

Classify user use cases into ONE specific category from the list below.

## Categories

### Communication
1. "writing emails" - Composing emails, responding to emails, email drafts
2. "sending messages" - Slack, Discord, iMessage, WhatsApp, Teams, SMS, chat messages
3. "social media" - Twitter/X posts, LinkedIn posts, social media comments

### Productivity & Work
4. "taking notes" - Note-taking, meeting notes, lecture notes
5. "writing documentation" - Technical docs, READMEs, wikis, internal documentation
6. "writing reports" - Business reports, PRDs, product specs, proposals
7. "task management" - To-do lists, task descriptions, project management updates
8. "braindump and creative thinking" - Brain dumping ideas, thinking out loud, ideation, brainstorming
9. "journaling" - Personal journaling, diary entries, self-reflection

### Coding & Development
10. "vibe coding" - Describing code to AI assistants (Cursor, Windsurf, Copilot), coding via voice, code comments, docstrings, commit messages, PR descriptions

### Content Creation
11. "writing articles" - Blog posts, articles, essays, long-form content
12. "creative writing" - Stories, fiction, scripts, creative projects
13. "academic writing" - Research papers, thesis, academic essays, citations

### Context-Based (When/Where)
14. "dictating while driving" - Using Wispr while driving, in the car, commuting
15. "dictating while walking" - Using Wispr while walking, exercising, on the go
16. "dictating in meetings" - Using during meetings, calls, video conferences
17. "working hands-free" - Hands-free scenarios, cooking, multitasking

### AI & Assistants
18. "prompting AI assistants" - ChatGPT, Claude, Gemini, AI chat interactions
19. "voice search" - Searching, looking things up, quick queries

### Other
20. "other" - Any use case that doesn't clearly fit the above categories

## CRITICAL RULES

- Only assign to categories 1-19 if you have HIGH CONFIDENCE (90%+ certain)
- If there is doubt or ambiguity, choose "other"
- The use case must be a CLEAR match to exactly ONE category

## Handling Ambiguous Cases

### Examples - Clear Category:

✅ "Writing emails"
   → "writing emails" (crystal clear)

✅ "Taking notes in Notion"
   → "taking notes" (clear activity)

✅ "Coding with Cursor"
   → "vibe coding" (AI-assisted coding)

✅ "Sending Slack messages"
   → "sending messages" (clear messaging)

✅ "Dictating while driving"
   → "dictating while driving" (clear context)

✅ "Writing PRDs"
   → "writing reports" (product specs = reports)

### Examples - Use "other":

❌ "General writing"
   → "other" (too vague - what kind of writing?)

❌ "Being productive"
   → "other" (not specific enough)

❌ "Using the app"
   → "other" (doesn't describe actual use case)

## Category Hierarchy

When a use case could fit multiple categories:
1. **Activity > Context**: "Writing emails while driving" → "writing emails" (activity is primary)
2. **Specific > General**: "Writing commit messages" → "git commits" (more specific than "writing documentation")
3. **Primary use > Secondary**: "Taking notes in meetings" → "taking notes" (the action, not just the context)
