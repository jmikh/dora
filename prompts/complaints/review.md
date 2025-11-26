# App Review Insight Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting insights about **Wispr Flow**, a voice-to-text dictation app, from app store reviews (App Store, Play Store, Trustpilot, Product Hunt, etc.). You will be given a single review and need to extract insights about Wispr Flow.

### What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

**CRITICAL RULES:**
1. Extract insights ONLY about **Wispr Flow** from the review
2. If a competitor app has issues, do NOT extract those as Wispr Flow complaints
3. Reviews are specifically about Wispr Flow, so assume all complaints/praise are about Wispr unless explicitly stated otherwise
4. Do NOT use the star rating - you must infer sentiment from the review text alone

## Output Schema

Return a JSON object with the following structure:

```json
{
  "competitors_mentioned": ["Competitor1", "Competitor2"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Brief description of complaint",
      "quote": "Exact quote from review"
    }
  ]
}
```

### Field Definitions:

- **competitors_mentioned**: List of competitor product names mentioned in the review
  - Examples: Spokenly, Vowen, FluidVoice, VoiceInk, Superwhisper, Talon, Dragon NaturallySpeaking, Siri, Willow Voice, Microsoft Dictation, etc.
  - Empty list if none mentioned

- **sentiment_score**: Integer from 1-5 representing sentiment **inferred from review text only**
  - 1 = Very negative (angry, frustrated, demanding refund, calling it unusable)
  - 2 = Somewhat negative (disappointed, multiple complaints, wouldn't recommend)
  - 3 = Neutral (mixed feelings, "it's okay", both pros and cons)
  - 4 = Somewhat positive (happy, works well, minor complaints)
  - 5 = Very positive (love it, game-changer, highly recommend, enthusiastic)
  - **IMPORTANT**: Do NOT look at the star rating - infer sentiment from the text alone

- **complaints**: List of specific problems or complaints **about Wispr Flow**
  - Each complaint must have a direct quote from the review
  - Include both explicit complaints ("X is broken") and implicit ones ("I wish it had Y" → complaint: "Lacks feature Y")
  - **IMPORTANT - Deduplication**: If multiple complaints are about the same core issue/topic, combine them into ONE complaint with the most representative quote
  - **IMPORTANT - Formatting**:
    - Keep complaint text SHORT (5-10 words max)
    - Use simple, jargon-free language
    - Remove app name (don't say "Wispr Flow")
    - Normalize for clustering (e.g., "Cannot disable AI formatting" not "Forced AI formatting cannot be disabled")
    - Make sure it is clear enough and can be understood if stand alone without additional context

---

## Few-Shot Examples

### Example 1: Very Negative with Multiple Critical Issues

**REVIEW:**

```
Title: Critical Bugs. Unusable. Avoid at All Costs.
Author: James Cockerill
Rating: 1 star
Source: App Store
Date: 2025-10-18

Wispr Flow was non-performant and terribly designed in Beta. It has somehow only gotten worse. Developers refuse to address long list of critical bugs. It is unquestionably the worst software application and most miserable User Experience I have ever come across in 20+ years as an Apple user and the team has shown a wanton disregard for addressing these issues it has been plagued with since its initial release. Instead, they have opted to invest all resources in further misleading Apple users with regard to its features and capabilities, charging a $15 subscription fee for negative value delivered. Apple needs to remove Wispr Flow from the App Store permanently.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 1,
  "complaints": [
    {
      "complaint": "Poor performance",
      "quote": "Wispr Flow was non-performant and terribly designed in Beta. It has somehow only gotten worse."
    },
    {
      "complaint": "Critical bugs not fixed",
      "quote": "Developers refuse to address long list of critical bugs"
    },
    {
      "complaint": "No customer support",
      "quote": "the team has shown a wanton disregard for addressing these issues"
    },
    {
      "complaint": "Too expensive for value",
      "quote": "charging a $15 subscription fee for negative value delivered"
    }
  ]
}
```

**Why this output?**
- Sentiment is 1 (very negative) - "worst software", "avoid at all costs", "unusable", extremely angry tone
- Multiple complaints about bugs, performance, support, pricing
- Deduplicated: All performance/design issues combined into one complaint
- Complaints are short, normalized, no app name

---

### Example 2: Very Negative - Won't Turn Off

**REVIEW:**

```
Title: DO NOT GET THIS APP!!!
Author: waterprise2
Rating: 1 star
Source: App Store
Date: 2025-10-09

I installed this app, and it works, BUT IT WON'T TURN OFF! If I just want to type, the app STILL puts in words from something else I'm listening to. I was writing an article on a historical event and watching a documentary for information on that topic. This app typed in what the TV was saying, even as I was typing. I've quit the app, but as soon as I click on something, it starts typing in what it's hearing no matter what I want to write. I wanted to put something in Google search, and it typed in words from an ad on the TV. I have to keep deleting what it writes. I've deleted the app, restarted my computer, DONE EVERYTHING and it STILL puts in words from elsewhere. I am at my wit's end. THIS APP WON'T GO AWAY!!!
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 1,
  "complaints": [
    {
      "complaint": "Cannot disable or turn off",
      "quote": "I've quit the app, but as soon as I click on something, it starts typing in what it's hearing no matter what I want to write"
    },
    {
      "complaint": "Picks up background audio",
      "quote": "This app typed in what the TV was saying, even as I was typing"
    }
  ]
}
```

**Why this output?**
- Sentiment is 1 (very negative) - ALL CAPS, multiple exclamation points, "at my wit's end", desperate tone
- Two distinct issues: can't turn off, picks up unwanted audio
- Short, normalized complaints

---

### Example 3: Negative - Cumbersome UX with Multiple Issues

**REVIEW:**

```
Title: cumbersome
Author: Iphonefeedback
Rating: 1 star
Source: App Store
Date: 2025-09-07

1. There is a significant delay between when I tap the hot key to start the program and when it starts to hear, which means I typically try to count to three or four between the Hot key and starting to talk. often I forget. Two, you can't see what you're typing until you click the button again which means you need to retap the hot key every time you want to check what you're writing. Three. On the computer it's hard to tell whether the dictation is on or not so I have often dictated for a while only to realize that all of the work was not recorded. 4. Unlike Microsoft dictation or dragon, you can't alternatively type, and then speak in order to edit or create bullet points etc without constantly needing to hit the hot keys for it to go off and on.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Microsoft Dictation", "Dragon"],
  "sentiment_score": 2,
  "complaints": [
    {
      "complaint": "Significant activation delay",
      "quote": "There is a significant delay between when I tap the hot key to start the program and when it starts to hear"
    },
    {
      "complaint": "No live preview while dictating",
      "quote": "you can't see what you're typing until you click the button again"
    },
    {
      "complaint": "Unclear recording status",
      "quote": "it's hard to tell whether the dictation is on or not so I have often dictated for a while only to realize that all of the work was not recorded"
    },
    {
      "complaint": "Cannot mix typing and dictation",
      "quote": "you can't alternatively type, and then speak in order to edit or create bullet points"
    }
  ]
}
```

**Why this output?**
- Sentiment is 2 (somewhat negative) - Multiple complaints, comparing negatively to competitors, but measured tone
- Four distinct usability issues
- Competitors mentioned as better alternatives
- Deduplicated: All hotkey issues kept separate as they describe different problems

---

### Example 4: Negative - No Support Response

**REVIEW:**

```
Title: Paid Subscription Locked Out — No Support Response
Author: dtepley
Rating: 1 star
Source: App Store
Date: 2025-09-05

I paid a lot of money for the annual subscription, got logged out, and now have no way to recover my account. The app forces me into a new free account, and support hasn't responded to multiple emails. I'm honestly flabbergasted, I've never had this lack of any customer support from any other product I have purchased. At this point, I'm forced to try to recover the cost through my credit card provider. I've moved to Willow Voice - they have much better customer
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Willow Voice"],
  "sentiment_score": 1,
  "complaints": [
    {
      "complaint": "Account login issues",
      "quote": "got logged out, and now have no way to recover my account. The app forces me into a new free account"
    },
    {
      "complaint": "No customer support response",
      "quote": "support hasn't responded to multiple emails. I'm honestly flabbergasted, I've never had this lack of any customer support"
    }
  ]
}
```

**Why this output?**
- Sentiment is 1 (very negative) - Lost access, no support, seeking refund, switched to competitor
- Two main issues: login bug and support
- Competitor mentioned as better alternative (switched to them)

---

### Example 5: Positive with Minor Complaint

**REVIEW:**

```
Title: Better than Siri for sure
Author: gagonzale
Rating: 5 stars
Source: App Store
Date: 2025-11-12

This app is amazing to have. I wish the keyboard was integrated better, but it understands all my medical terminology and the the way I speak, it's amazing.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Siri"],
  "sentiment_score": 5,
  "complaints": [
    {
      "complaint": "Poor keyboard integration",
      "quote": "I wish the keyboard was integrated better"
    }
  ]
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "amazing" used twice, "better than Siri", enthusiastic
- One minor complaint about keyboard integration
- Siri mentioned as inferior competitor

---

### Example 6: Very Positive - Game Changer

**REVIEW:**

```
Title: I used to be extremely skeptical
Author: Victoria Liang
Rating: 5 stars
Source: Product Hunt
Date: 2025-11-16

I used to be extremely skeptical of voice-to-text. I type so fast, and I was used to all the options being extremely inaccurate. Wispr Flow changed everything, and I'm a believer now. No matter how fast you type, it's a total gamechanger for prompting ChatGPT with more context or answering texts while walking. They also recently added snippets, which let me just say a command instead of typing or copying + pasting the same things over and over.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 5,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "changed everything", "I'm a believer", "total gamechanger"
- No complaints mentioned
- Went from skeptical to believer (strong positive conversion)

---

### Example 7: Very Positive - Writing This Review With It

**REVIEW:**

```
Title: Efficient and effective speech-to-text app.
Author: B a BOSS
Rating: 5 stars
Source: App Store
Date: 2025-11-13

I've been using Wispr Flow for a month now, and it helps me generate more ideas and keep workflow moving at a faster rate. I wrote this review with Wispr Flow.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 5,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "efficient and effective", actively using it to write the review itself (strong endorsement)
- No complaints mentioned

---

### Example 8: Positive with Understanding of Learning Curve

**REVIEW:**

```
Title: interesting
Author: Davejto
Rating: 5 stars
Source: App Store
Date: 2025-11-14

works great, I think the challenge is changing my own behavior
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 4,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 4 (somewhat positive) - "works great" but brief, not super enthusiastic, acknowledges challenge
- No complaints about the app itself (challenge is user behavior change, not a product issue)

---

### Example 9: Very Positive - Love the Accuracy and Patience

**REVIEW:**

```
Title: Such a nice improvement to regular speech-to-text.
Author: Rob Brogan
Rating: 5 stars
Source: App Store
Date: 2025-11-12

I'm writing this using the app! I'll be honest that I'm pretty skeptical of a lot of AI tools, but there are certain things, such as summarizing long documents, and in this case, getting closer to my real intent when trying to dictate something, that are really great uses for AI. I love the accurate punctuation and its patience when I stop or fumble with my thinking out loud.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 5,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "I love", writing review with the app, converted skeptic to believer
- No complaints mentioned

---

### Example 10: Positive - Finally Solved My Problem

**REVIEW:**

```
Title: Finally.
Author: DaveRecruiter
Rating: 5 stars
Source: App Store
Date: 2025-11-12

I'm always on the go and working from my phone. So it's fantastic to finally have an option to talk and walk and get work done without having to worry about constantly looking at the screen to format my messaging.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 5,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 5 (very positive) - "fantastic", "finally" (solved a longstanding problem)
- No complaints mentioned

---

## Now Extract Insights from This Review:

[REVIEW WILL BE PROVIDED HERE]
