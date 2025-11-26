# Reddit POST Insight Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting insights about **Wispr Flow**, a voice-to-text dictation app, from Reddit posts. You will be given a single Reddit post (title + body) and need to extract insights about Wispr Flow.

### What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

**CRITICAL RULES:**
1. Extract insights ONLY about **Wispr Flow** from the post
2. If a competitor app has issues, do NOT extract those as Wispr Flow complaints
3. If sentiment is not about Wispr Flow, return `null` for sentiment_score
4. Use context clues (subreddit, post content) to determine if complaints/features are about Wispr

## Output Schema

Return a JSON object with the following structure:

```json
{
  "competitors_mentioned": ["Competitor1", "Competitor2"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Brief description of complaint",
      "quote": "Exact quote from post"
    }
  ]
}
```

### Field Definitions:

- **competitors_mentioned**: List of competitor product names mentioned in the post
  - Examples: Spokenly, Vowen, FluidVoice, VoiceInk, Superwhisper, Talon, Dragon NaturallySpeaking, Siri, Noteflux, etc.
  - Empty list if none mentioned

- **sentiment_score**: Integer from 1-5 representing sentiment **about Wispr Flow only**
  - 1 = Very negative about Wispr Flow
  - 2 = Somewhat negative about Wispr Flow
  - 3 = Neutral about Wispr Flow (has opinion but mixed/balanced)
  - 4 = Somewhat positive about Wispr Flow
  - 5 = Very positive about Wispr Flow
  - **null** = No sentiment expressed OR purely factual/informational content (e.g., questions asking for help, feature announcements, how-to posts, technical discussions without opinion)
  - **IMPORTANT**: Only assign a sentiment score if the post expresses an OPINION or FEELING about Wispr Flow. Neutral questions, informational posts, and factual discussions should return null.

- **complaints**: List of specific problems or complaints **about Wispr Flow**
  - Each complaint must have a direct quote from the post
  - Only extract if clearly about Wispr Flow (use subreddit/context to determine)
  - If post is in r/WisprFlow or clearly discussing Wispr, extract complaints even without explicit "Wispr" mentions
  - Include both explicit complaints ("X is broken") and implicit ones ("I wish it had Y" → complaint: "Lacks feature Y")
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
    - Include specific feature/setting names from the post content

---

## Few-Shot Examples

### Example 1: Strong Negative Sentiment with Multiple Complaints

**POST:**

```
Title: Wispr Flow is a scam
Body: I feel like I wasted my money on their annual plan. When I first got Wisprflow, I thought it was awesome, but it's just gotten so bad recently. has anyone felt the same??

The app constantly glitches. One minute it works, the next it freezes or disconnects for no reason. I've had it randomly stop during important notes, and sometimes it says it can't connect even though my WiFi is fine.

Also, it seems to be a really clunky electron app. It's always taking up a massive chunk of my computer's memory and slows everything down. It's extremely resource-intensive, especially given the fact that it's always going to be on in the background.

I've requested for support like a million times, but no one ever responds. I've given up on the product for the past couple of weeks. Recently, I've been looking and exploring some new ones.

I still really like the idea behind it, so I'm looking for something that actually works. Here are some better options I've found. When researching these, I specifically only looked for the ones that were built natively for Mac:

**Voice Ink**: Fantastic for people who want control and power-mode switching. One-time payment, local models, and a solid dev support.

**Super whisper**: Best for power users who want full control and unlimited AI processing. Also one-time payment, with local models.

**Willow Voice**: The devs here are amazing. They respond in minutes and fix things quickly. Mac native app. It's subscription-based, which I don't love, but it's the fastest and most accurate dictation tool I've used. Formatting for emails is spot on, which I haven't seen from the others.

Community: r/ChatGPT
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Voice Ink", "Super Whisper", "Willow Voice"],
  "sentiment_score": 1,
  "complaints": [
    {
      "complaint": "Frequent glitches and crashes",
      "quote": "The app constantly glitches. One minute it works, the next it freezes or disconnects for no reason"
    },
    {
      "complaint": "Connection issues",
      "quote": "sometimes it says it can't connect even though my WiFi is fine"
    },
    {
      "complaint": "Uses too much memory",
      "quote": "it seems to be a really clunky electron app. It's always taking up a massive chunk of my computer's memory and slows everything down"
    },
    {
      "complaint": "No customer support",
      "quote": "I've requested for support like a million times, but no one ever responds"
    },
    {
      "complaint": "Not native Mac app",
      "quote": "I specifically only looked for the ones that were built natively for Mac"
    },
    {
      "complaint": "No one-time payment option",
      "quote": "Voice Ink: Fantastic for people who want control and power-mode switching. One-time payment, local models"
    }
  ]
}
```

**Why this output?**
- Sentiment is 1 (very negative) - "scam", "wasted my money", multiple complaints
- Deduplicated: "glitches, freezes, disconnects" + "randomly stops" are all stability issues, combined into one
- Deduplicated: "Clunky Electron" + "resource-intensive" both about memory/performance, combined into one
- Deduplicated: "Zero support" + "Lacks responsive support" are same topic, combined into one
- Complaints are short (2-5 words), normalized, no app name, ready for clustering

---

### Example 2: Mostly Positive with One Complaint

**POST:**

```
Title: Wispr Flow and alternatives
Body: I got Wispr Flow about two months ago, and after using it for a few weeks, I signed up for the subscription. The thing that did it for me was how it recognizes when I make a mistake and fixes it. Do any of the other alternative voice-to-text apps do that? And for those who've never tried Wispr Flow or don't understand what I'm talking about this is what I mean.

When I use the apple built-in voice to text and said something like "hey Steve, let's meet tomorrow at 4 PM no I'm sorry 3 PM at that new restaurant in downtown Indianapolis I'm sorry Baltimore and have lunch and discuss the new talent bench" It would type it out for word.

However, when I use Wispr Flow and say the same thing, it would correct it to "Hey Steve, let's meet tomorrow at 3PM at that new restaurant in downtown Baltimore and have lunch and discuss the new Talent Bench."

I've tried Spokenly, the Apple Wispr app, and one other one that I can't remember, and none of them do that. Is there one that does?

I am 99.9% happy with Wispr Flow. There was a bug like a month ago where it wouldn't catch the first or second word. But other than that, they fixed that., I've not had a single issue with it, and it works amazing, including the snippets and the dictionary as well. They just upgraded it to allow you to customize it to talk more casually via text message, and more formally via email or documents or whatever you choose depending on the platform you're talking.

Correcting my grammar, spelling, and mistakes like that is amazing to me. And that's why I was wondering if any of the other apps did it.

Community: r/ProductivityApps
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Spokenly", "Apple Voice to Text"],
  "sentiment_score": 5,
  "complaints": [
    {
      "complaint": "Missed first words",
      "quote": "There was a bug like a month ago where it wouldn't catch the first or second word"
    }
  ]
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "99.9% happy", "works amazing", "amazing to me"
- Only one complaint mentioned (and it was fixed)
- Competitors mentioned but only to show Wispr is better than them

---

### Example 3: Very Positive with Complaint and Feature Request

**POST:**

```
Title: Wispr Flow with wireless mic and Mac in clamshell mode.
Body: I love WisprFlow and subscribed immediately after seeing the potential for vibe coding, and sure enough, it has boosted my coding rates like 10x because I can now provide more ample context to Claude and its precision has increased like 100 times when solving coding problems, because I can now describe a complete scenario and AI takes it from there. So now instead of generating useless code, it can create precise code that solves the issue right at the first try 95% of the time.

However, there's a big problem that I think Wispr Flow hasn't solved yet. I tried to use it with my AirPods, and them being Bluetooth, it doesn't understand anything I say at all. I have to revert back to using my laptop and speaking to the internal microphone. This is annoying because sometimes I need to use my monitors and put my Mac in clamshell mode. But putting it in clamshell mode makes the internal microphone not work properly and I'm being forced between using my monitors or WisprFlow.

I was thinking about buying a wired USB-c lapel microphone, but all the cables are really long and quite cumbersome to be sitting down and getting my microphone on and off if I have to move from my desk to somewhere else. Then I saw a cheap wireless microphone that plugs into the USB port and the mic on my lapel.

This is no Bluetooth, seems to be RF and have much less delay than BT, will it work with Wispr Flow, or will it be a complete failure? Guess I will have to buy a couple of different microphones and see which one works. But should it forcefully be a wired microphone?

I really love Wispr Flow out of all the dictation apps I tried. I am recommending it to all my friends and co-workers because this thing is making us go many times faster than just typing. AI gets really powerful when used with Wispr Flow because you are giving it way more context than simply typing stuff and it helps you solve problems right about 95% of the time as I said before. Also Wispr Flow is one of the few apps that really gets it right the first time you say it compared to others, (particularly Siri), that understand nothing at all or invent words you didn't even say.

Any tips you have so I can use Wispr Flow with wireless microphones? Or a practical wired mic that you know works properly with my Mac in clamshell mode and dictating from about two feet away?

I'll make some experiments and report back as soon as I find out what works...

UPDATE EDIT: Cheap chinese wireless lapel mics with RF receiver worked great because they are RF and limited to bluetooth bandwidth, check my reply below for the links on the mics I did my experiment with.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Siri"],
  "sentiment_score": 5,
  "complaints": [
    {
      "complaint": "Poor Bluetooth microphone support",
      "quote": "I tried to use it with my AirPods, and them being Bluetooth, it doesn't understand anything I say at all"
    },
    {
      "complaint": "Doesn't work in clamshell mode",
      "quote": "putting it in clamshell mode makes the internal microphone not work properly"
    }
  ]
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "I love WisprFlow", "boosted my coding rates like 10x", "I am recommending it to all my friends"
- Deduplicated: "Doesn't work with Bluetooth" and "Lacks better Bluetooth support" are same topic, combined into one
- Deduplicated: "Internal mic in clamshell mode" and "Lacks clamshell mode support" are same topic, combined into one
- Complaints are short, normalized, no app name
- Even though very positive, still has legitimate technical issues

---

### Example 4: Competitor Comparison (Wispr Mentioned Positively)

**POST:**

```
Title: I built a free-forever alternative to Wispr Flow
Body: Hey everyone 👋,

My brother and I have been building a macOS app called Vowen. It is a speech to text and AI supported writing tool built on Whisper.cpp / Parakeet with optional support for local and cloud models. Everything can run locally and you only use the cloud if you choose to add your own API key.

**Why we built it**

Both of us use AI tools constantly for coding, writing, planning and general problem solving. Over time it felt more natural to just speak instead of typing long prompts or explanations. We regularly dictate into Cursor and ChatGPT and that easily ends up being five to eight thousand words a week.

We originally used Whisper Flow and paid for the subscription because it worked well. Eventually we realized that with Whisper.cpp and lightweight models running locally we could have similar accuracy and speed directly on our own machines without depending on a service.

So we started building our own workflow tool, mostly because it made daily work easier and because we enjoy building it. Since it is powered by open source components and something we want to keep experimenting with, we decided to make it free forever.

**What it does today**

The focus is on quickly getting ideas into tools you already use, not replacing deep writing. It helps with things like:

• Dictating prompts into Cursor, ChatGPT or any other AI tools
• Writing messages and replies in Slack or Discord
• Drafting emails in Gmail
• Rewriting or shortening selected text
• Recording meetings and generating summaries
• Voice commands to open apps or trigger simple actions
• Using either local models or your own cloud API key

It is meant to reduce friction when moving from thought to action rather than replace long form writing tools.

**Roadmap**

We are currently working on:

• Support for Windows
• More voice driven workflows for interacting with apps

**Feature requests**

We are actively building based on what users ask for. You can send suggestions here:

[https://vowen.featurebase.app/](https://vowen.featurebase.app/)

Happy to answer questions and would love to hear how you would use a local voice interface in your workflow.

Community: r/macapps
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Vowen"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "No local model support",
      "quote": "Everything can run locally and you only use the cloud if you choose to add your own API key"
    },
    {
      "complaint": "No one-time payment option",
      "quote": "we decided to make it free forever"
    }
  ]
}
```

**Why this output?**
- Sentiment is 4 (somewhat positive) - They say "it worked well" and used it before building alternative
- No explicit complaints stated
- Deduplicated: "local models" and "bring your own API key" are related to offline/cost control, combined into "No local model support"
- Complaints are short, normalized, no app name

---

### Example 5: Null Sentiment (Not About Wispr)

**POST:**

```
Title: Alternative to wisprflow
Body: Hey everyone — we've been building this desktop app for a while and finally launched Noteflux. Typing slows you down, so we built something better: Noteflux lets you write in any app using your voice — it formats, fixes typos and grammar, and even understands what you meant to say. You can also customise how it writes.
We'd love brutal feedback from users so we can keep improving it.
👉 https://noteflux.app/

Community: r/macapps
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Noteflux"],
  "sentiment_score": null,
  "complaints": []
}
```

**Why this output?**
- Sentiment is **null** - This is a promotional post for Noteflux, not about Wispr
- Title says "Alternative to wisprflow" but post body doesn't discuss Wispr at all
- No complaints to extract because post doesn't evaluate or discuss Wispr
- Competitor mentioned: Noteflux

---

### Example 6: Neutral Question (No Sentiment)

**POST:**

```
Title: How to dictate without formatting?
Body: Hi guys! Is there a way I can dictate and use Wispr Flow without formatting? The issue is that for some cases, I will have to just dictate the text in one box, and I don't want to separate it or format it in any way. Unfortunately, I wasn't able to turn it off, so is there a solution for this?

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": null,
  "complaints": [
    {
      "complaint": "Cannot disable formatting",
      "quote": "I don't want to separate it or format it in any way. Unfortunately, I wasn't able to turn it off"
    }
  ]
}
```

**Why this output?**
- Sentiment is **null** - This is a neutral help question, not expressing an opinion about the product
- User is asking for help with a feature, not expressing satisfaction or dissatisfaction
- No words like "frustrated", "love", "hate", "amazing", "terrible" - just a factual question
- Complaint IS extracted because it identifies a real issue (can't disable formatting)
- **Key distinction**: You can extract complaints from neutral questions, but don't assign sentiment unless opinion/feeling is expressed

---

## Now Extract Insights from This Post:

[POST WILL BE PROVIDED HERE]
