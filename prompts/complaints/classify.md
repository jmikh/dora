# Complaint Classification Prompt for Wispr Flow

## About Wispr Flow

Wispr Flow is a voice dictation app that allows users to convert speech to text across various applications. Users commonly use it for:
- Writing emails (Gmail, Outlook, Superhuman)
- Messaging (Slack, Discord, iMessage, WhatsApp, Teams)
- AI prompting (ChatGPT, Claude, Cursor, Windsurf)
- Coding assistance ("vibe coding" - describing code to AI assistants)
- Note-taking (Notion, Obsidian, Apple Notes, brain dumping ideas)
- Documentation (writing docs, creating content)

The app works by capturing voice input, transcribing it using AI, and optionally applying Smart Formatting/AI editing before inserting the text into the target application.

## Your Task

Classify user complaints into ONE specific category from the list below.

## Categories

1. "lag in starting recording" - Delays or lag when initiating voice recording, slow to start listening
2. "latency in transcription" - Slow transcription speed, delays in seeing text appear, long processing times
3. "no dark mode" - Missing dark mode feature, UI appearance customization requests
4. "customer support not responsive" - Unresponsive support team, no reply to tickets, poor customer service
5. "too expensive" - Pricing concerns, subscription cost complaints, value for money issues
6. "microphone runs in the background" - Microphone stays active when not needed, always-on concerns, no auto-off
7. "drains battery or high cpu usage" - Battery drain issues, high CPU usage, performance impact on device
8. "freezes and crashes" - App freezing, crashing, hanging, becoming unresponsive
9. "no offline or local model" - Requires internet connection, no offline mode, no local processing option
10. "issues with command mode" - Command Mode not working, server busy errors, command recognition failures
11. "accuracy issues" - Transcription errors, wrong words, misrecognition, poor quality output
12. "AI/Smart formatting issues" - Problems with AI formatting, cannot disable Smart Formatting, unwanted edits
13. "privacy concerns" - Data privacy worries, security concerns, data storage/usage questions
14. "language detection issues" - Wrong language detected, multi-language mixing, language switching problems
15. "punctuation issues" - Missing punctuation, wrong punctuation, capitalization errors
16. "keyboard issues" - Missing keyboard features, incomplete mobile keyboard, switching keyboards
17. "hotkey issues" - Keyboard shortcut conflicts, cannot bind shortcuts, hyper-key problems, key combinations not working
18. "reliability and performance problems" - General instability, unreliable app, poor optimization, inconsistent behavior
19. "subscription problems" - Billing issues, trial not working, refund requests, activation problems, subscription errors
20. "customization issues" - Cannot customize styles/templates/prompts, limited to preset options, no per-app personalization
21. "authentication and login issues" - Cannot login, white screen on sign-in, verification code not received, authentication failures
22. "onboarding issues" - Confusing onboarding, repeats on every login, cannot skip setup flow, wizard doesn't detect completion
23. "microphone compatibility issues" - Microphone not working with specific hardware, external mic not detected, AirPods/headset issues
24. "lack of Android version" - No Android app, Android support requests, platform availability complaints
25. "lack of public roadmap or feature requests" - No visibility into upcoming features, feature requests ignored, no public roadmap
26. "no better than competitors" - Complaints that Wispr is not better than alternatives, unfavorable comparisons to other apps
27. "issues related to updates" - Problems after updating, update broke functionality, update-related bugs, version issues
28. "difficult to use" - Confusing UI, poor UX, hard to learn, unintuitive interface, usability complaints
29. "other" - Any complaint that doesn't clearly fit the above categories

## CRITICAL RULES

- Only assign to categories 1-28 if you have Relatively HIGH CONFIDENCE (85%+ certain)
- If there is High doubt or ambiguity, choose "other"
- The complaint must be a CLEAR, OBVIOUS, UNAMBIGUOUS match to exactly ONE category

## Handling Multiple Possible Categories

When a complaint could fit multiple categories, choose the MOST SPECIFIC category:

### Examples - Choose Most Specific:

✅ "Microphone runs in background and I'm worried about privacy"
   → "microphone runs in the background" (specific technical issue)
   NOT "privacy concerns" (too general)

✅ "Command Mode is too slow"
   → "issues with command mode" (specific feature problem)
   NOT "latency in transcription" (too general)

✅ "Battery drains because mic won't turn off"
   → "microphone runs in the background" (root cause)
   NOT "drains battery or high cpu usage" (symptom)

✅ "Support never replied about my refund request"
   → "customer support not responsive" (primary issue)
   NOT "too expensive" (not the main complaint)

✅ "App crashes when transcribing long texts"
   → "freezes and crashes" (main problem)
   NOT "accuracy issues" (not relevant)

✅ "No local model available for privacy"
   → "no offline or local model" (specific feature request)
   NOT "privacy concerns" (too general)

### Examples - Clear Single Category:

✅ "Transcription has many spelling mistakes"
   → "accuracy issues" (crystal clear)

✅ "Support team never replied to my ticket"
   → "customer support not responsive" (obvious)

✅ "Takes 30 seconds to show text after speaking"
   → "latency in transcription" (unambiguous)

✅ "Cannot disable AI formatting"
   → "AI/Smart formatting issues" (specific)

✅ "Detects French when I'm speaking English"
   → "language detection issues" (clear)

### Examples - Use "other":

❌ "App doesn't work"
   → "other" (too vague)

❌ "Slow and inaccurate and crashes"
   → "other" (multiple unrelated issues with equal weight)

❌ "Hard to use"
   → "other" (unclear what the problem is)

❌ "Need better features"
   → "other" (generic, not specific)

❌ "No mobile keyboard"
   → "other" (feature not in our categories)

## Hierarchy of Specificity

- Specific technical problem > General category
- Root cause > Symptom
- Feature-specific issue > General performance issue
- Concrete behavior > Abstract concern
