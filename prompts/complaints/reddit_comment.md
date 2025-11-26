# Reddit Insight Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting insights about **Wispr Flow**, a voice-to-text dictation app, from Reddit conversations. You will be given a Reddit thread with context (parent comments and the root post) followed by a TARGET comment that you need to analyze.

### What is Wispr Flow?

Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)

**CRITICAL RULES:**
1. **Extract insights ONLY from the TARGET comment** (the last comment in the thread)
2. The context (parent comments and post) is provided ONLY to help you understand the conversation
3. **DO NOT extract insights from the context** - only from the TARGET comment
4. Only extract insights that are **specifically about Wispr Flow**
5. If a competitor app has issues, do NOT extract those as Wispr Flow complaints
6. If sentiment is not about Wispr Flow, return `null` for sentiment_score

## Output Schema

Return a JSON object with the following structure:

```json
{
  "competitors_mentioned": ["Competitor1", "Competitor2"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Brief description of complaint",
      "quote": "Exact quote from TARGET comment"
    }
  ]
}
```

### Field Definitions:

- **competitors_mentioned**: List of competitor product names mentioned in the TARGET comment
  - Examples: Spokenly, Vowen, FluidVoice, VoiceInk, Superwhisper, Talon, Dragon NaturallySpeaking, Siri, etc.
  - Empty list if none mentioned

- **sentiment_score**: Integer from 1-5 representing sentiment **about Wispr Flow only** in the TARGET comment
  - 1 = Very negative about Wispr Flow
  - 2 = Somewhat negative about Wispr Flow
  - 3 = Neutral about Wispr Flow (has opinion but mixed/balanced)
  - 4 = Somewhat positive about Wispr Flow
  - 5 = Very positive about Wispr Flow
  - **null** = No sentiment expressed OR purely factual/informational content (e.g., support responses, feature explanations, how-to answers, neutral questions)
  - **IMPORTANT**: Only assign a sentiment score if the comment expresses an OPINION or FEELING about Wispr Flow. Factual statements, support answers, and informational responses should return null.

- **complaints**: List of specific problems or complaints **about Wispr Flow** mentioned in TARGET comment
  - Each complaint must have a direct quote from the TARGET comment
  - Only extract if clearly about Wispr Flow (use thread context to determine)
  - If the thread is in r/WisprFlow or clearly discussing Wispr, extract complaints even without explicit "Wispr" mentions
  - Include both explicit complaints ("X is broken") and implicit ones ("I wish it had Y" → complaint: "Lacks feature Y")
  - **IMPORTANT - Use Thread Context to Enrich Complaints**: If the TARGET comment mentions "it", "this", "the setting", etc., look at the thread context to identify the specific feature/setting being discussed and include it in the complaint text
    - ❌ BAD: "Unclear how to toggle setting"
    - ✅ GOOD: "Unclear how to toggle Smart Formatting"
    - ❌ BAD: "Feature doesn't work"
    - ✅ GOOD: "Bluetooth microphone doesn't work"
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
    - Include specific feature/setting names when the context reveals them (even if TARGET comment uses pronouns)

---

## Few-Shot Examples

### Example 1: Multiple Competitors Mentioned

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Is Wispr Flow worth it?
Body: Hey guys, I was just wondering if Wispr Flow is worth paying for. Currently with the student discount and everything, I believe comes up to $6 USD per month, which is about $8.25 CAD per month. At least that's for me and the price that it's given me on the Wispr Flow app. Just wanted to know your thoughts.
```

**TARGET COMMENT:**

```
Only you can tell if it's worth it for you. Is it a good app? Yes. Are there good alternatives? Yes. Can you do the same for free? Yes.

It really depends on what you need and whether you're more technical and like dealing with prompts and settings/need customization. Spokenly is a solid alternative that can do a lot of what Wispr Flow does—free if you use local models or bring your own API keys. There's also Ito AI, which is basically an open-source copy of Wispr Flow (less powerful, but maybe you don't need "powerful" right now). If you need more power and customization there's VoiceInk, Superwhisper (my favorite), and a bunch more.

Honestly, there are A LOT of alternatives.

EDIT. BTW. If you are looking for something that is iOS as well, then your options will be a bit more limited. Wispr Flow/Spokenly/Superwhisper. Out of those three my fav on iOS is Spokenly, but Superwhisper has a new version on Testflight and it's really nice—not sure when will it be released. There's also VoiceInk for iOS but last I tried it was too buggy, perhaps it's better now.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Spokenly", "Ito AI", "VoiceInk", "Superwhisper"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "No local model support",
      "quote": "Spokenly is a solid alternative that can do a lot of what Wispr Flow does—free if you use local models or bring your own API keys"
    },
    {
      "complaint": "Limited customization options",
      "quote": "If you need more power and customization there's VoiceInk, Superwhisper (my favorite), and a bunch more"
    }
  ]
}
```

**Why this output?**
- Sentiment is 4 (positive) because they say "Is it a good app? Yes"
- Extracted implicit complaints from competitor comparisons (what Wispr is missing)
- When they say competitors are better because of X, it means Wispr lacks X → complaint

---

### Example 2: Positive Sentiment with Praise

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Wispr Flow has been insanely accurate and good for transcribing
Body: Been using Wispr Flow for a few weeks. It's super accurate at live transcription. I code by talking, even in noisy cafes, and it still gets most words right. Its been helping me get ideas out fast, stay focused, and then clean things up while the AI writes the boring parts. I'm definitely getting more done.

[COMMENT - CONTEXT]
That's very interesting, but what makes this much better than a free app like Spokenly? Spokenly, you can use it 100% for free with the local models and you can even bring your own API keys so that you're charged as you go for much cheaper based on your own personal usage. Looking at the price comparison for the subscription for wispr flow and Spokenly, it seems like wispr flow is a little bit more expensive. For Spokenly, you only pay if you want to use their online cloud services, but using it locally and or using your own API key is much cheaper and oftentimes free. So why should I choose wispr flow over something like Spokenly? What makes wispr flow so great?
```

**TARGET COMMENT:**

```
I personally havent tried out Spokenly, but I did try out Superwhisper and Wispr Flow which are two of the biggest names right now.

Among the 2, Wispr Flow was actually just super fast for me, almost instantaneous results and great for tagging files in cursor as well. I wasnt able to get the same accuracy with Superwhisper

Again, havent tried Spokenly but just wanted to mention the benefits for this. They have a 1 month trial available if you'd like to check it out for yourself - [Download Wispr Flow](https://ref.wisprflow.ai/wispr)

Also they have a 2000 words/week limit if you want to check out the performance, etc
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Spokenly", "Superwhisper"],
  "sentiment_score": 5,
  "complaints": []
}
```

**Why this output?**
- Sentiment is 5 (very positive) because they praise Wispr as "super fast" with "instantaneous results" and "great accuracy"
- No complaints mentioned in target comment
- Even though Spokenly and Superwhisper are mentioned, no complaints about Wispr are extracted

---

### Example 3: Feature Requests with Context

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: [Feature Request] Cloud Sync for Transcription History Across Devices
Body: Hey Wispr Flow team and community! I'd love to see cloud sync functionality added for our transcription history. Right now, each device stores everything locally, and I think having our transcripts synced across all devices would be a game-changer.
```

**TARGET COMMENT:**

```
Thank you so much for getting back to me and starting the conversation.

First of all, I think that it could be useful simply from a storage perspective. Storing everything locally adds up pretty quickly.

Secondly, from a history perspective, I personally always go back to my history and either look at what I previously typed to remember what I was working on, or if I lose access to something or accidentally forget where and what I did with something that I typed. It makes it super easy just to go to my transcription history and see exactly what I typed. Thirdly, to be able to copy things that I said previously that I may want to say again without having to restate or rewrite them for memory.

Third of all, I think this opens the door to more personalization. If you store the transcription history, you can use it as training data to make a more custom, fine-tuned model for each user. The transcription in AI Polish is more tailored towards their style, vocabulary, and preferences, making it a more magical experience for the user. I understand that all users may not want this, but for the ones that do, it could be good to have.

And finally, yes, I would love to have the ability to search my old notes, maybe for the past week or month. I sometimes have a vague recollection of me previously writing something, and being able to go back and check would be extremely helpful.

Finally, for the mobile-to-desktop users, I think an instant sync would be extremely helpful for everyone who's not on a Mac. Syncing what you have on mobile to desktop is a little difficult. If you could almost recreate that with your app I think it can be really helpful. The way I imagine it is I could voice-type something on my phone and then paste it on my laptop. This could be especially useful in situations where you can't verbally speak to your laptop out loud, but you can quietly whisper into the bottom of your phone.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Local storage fills up quickly",
      "quote": "Storing everything locally adds up pretty quickly"
    },
    {
      "complaint": "No cloud sync across devices",
      "quote": "Syncing what you have on mobile to desktop is a little difficult"
    },
    {
      "complaint": "No search for old transcriptions",
      "quote": "I would love to have the ability to search my old notes, maybe for the past week or month"
    },
    {
      "complaint": "No personalized AI model",
      "quote": "If you store the transcription history, you can use it as training data to make a more custom, fine-tuned model for each user"
    }
  ]
}
```

**Why this output?**
- Sentiment is 4 (positive) because tone is enthusiastic and constructive
- Thread context makes it clear this is about Wispr Flow
- Deduplicated sync-related complaints: "No cloud sync" and "Lacks instant mobile-to-desktop sync" are the same topic, so combined into one
- Complaints are short, normalized, jargon-free (no "Wispr Flow" in text)
- Converted feature requests to "No X" complaints with exact quotes

---

### Example 4: Negative Sentiment and Criticism

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Introducing r/WisprFlow. Let's make Flow better together!
Body: Hey everyone! I'm Victoria with Wispr Flow. We make voice-to-text that's fast, accurate, secure, and works on all your apps (Gmail, Slack, ChatGPT, Notion, Cursor). We want to remove the hassle of typing so you can answer emails, write detailed AI prompts, or brain dump ideas as naturally as talking.

[COMMENT - CONTEXT]
Did you ever consider using tools like Canny for feature request management, like all the other tools out there? This makes it much easier for us to find similar requests and vote them up, or to enter a new request and see all the requests already created under this topic. Also, you can request a feature in progress or include it in something like a roadmap that everyone wants to see. This is also possible with tools like Canny. There are various tools available. This is not sponsored, just an idea.

[COMMENT - CONTEXT]
Hey u/BENC-win thanks for the suggestion! Currently, I'm letting people submit feature requests or questions as new posts just because we're trying to build some momentum on the subreddit. Right now, we don't even meet the minimum threshold of activity for the subreddit to be "reviewed" and to load in mobile web without getting an error saying "Unreviewed Content: This community has not been reviewed and might contain content inappropriate for certain viewers." Once we get a minimum threshold of activity, I plan to start doing Weekly or Monthly Feedback and Feature Request threads, so everything is in consolidated in one place and we have fewer duplicate posts. Users would also be able to upvote requests they agree with as well. Some of my previous companies have used Canny so I'm familiar with the tool, but I want to try having all of the dialogue on Reddit for now for more authenticity, community-building, and native discovery. That being said, we'll be doing lots of experimentation and might switch over in the future.
```

**TARGET COMMENT:**

```
u/VictoriaAtWispr, I appreciate your reply!

I understand that you want to use Reddit to gain more visibility. However, in my view, it's the wrong approach to prioritize promotion over user intention. The goal should be to make it as easy as possible for users to provide feedback and suggest improvements. A great product generates visibility on its own — satisfied users will happily share their experiences.

Remember your customer: The perfect tool should save time and effort. We are highly efficient people who want to save time and work as effectively as possible in general. Having to create a Reddit account just to give feedback on another tool and searching for subreddits, while reading each one to find the one with the same intent, feels like an unnecessary hurdle. I am absolutely against the idea of using Wispr in this manner.

In the end, this unfortunately comes across as yet another unconventional path Wispr is taking — one that risks slowing things down rather than accelerating growth. On top of that, Reddit offers weaker structure and discoverability for such matters (which might be a reason tools like Canny exist). There's no roadmap transparency, and if activity really does scale, things will quickly become completely unmanageable.

I use Wispr because it's really fast, but other tools are emerging quickly, and they have features I absolutely miss in Wispr. I hope you will be ahead in that race.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 2,
  "complaints": [
    {
      "complaint": "Feedback process too cumbersome",
      "quote": "Having to create a Reddit account just to give feedback on another tool and searching for subreddits, while reading each one to find the one with the same intent, feels like an unnecessary hurdle"
    },
    {
      "complaint": "No public roadmap",
      "quote": "There's no roadmap transparency, and if activity really does scale, things will quickly become completely unmanageable"
    },
    {
      "complaint": "Missing features vs competitors",
      "quote": "other tools are emerging quickly, and they have features I absolutely miss in Wispr"
    }
  ]
}
```

**Why this output?**
- Sentiment is 2 (somewhat negative) because they express frustration with approach and mention missing features
- They do say "I use Wispr because it's really fast" (positive) but overall tone is critical (negative)
- Deduplicated: "Lack of roadmap transparency" and "Lacks public roadmap" are same topic, combined into one
- Deduplicated: "Lacks dedicated feature request tool" is about feedback process, combined with cumbersome feedback complaint
- Complaints are short, normalized, no app name
- No competitors explicitly named in target comment

---

### Example 5: No Wispr Sentiment (Should Return Null)

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: I built a free-forever alternative to Wispr Flow
Body: Hey everyone, my brother and I have been building a macOS app called Vowen. It is a speech to text and AI supported writing tool built on Whisper.cpp / Parakeet with optional support for local and cloud models. Everything can run locally and you only use the cloud if you choose to add your own API key.

[COMMENT - CONTEXT]
Always nice, another free STT app! But we already have Spokenly and FluidVoice for example. Both are free too. What improvements does Vowen bring? Since you build support for Windows, is Vowen an Electron app?
```

**TARGET COMMENT:**

```
Thanks! I haven't used Spokenly or FluidVoice myself so I can't compare directly. I assume they use Whisper.cpp or Parakeet so in terms of transcription speed and accuracy it's probably similar.

From quickly looking at their feature lists we overlap on most core features. The main things that currently stand out in Vowen that I can say are:

1. Generating summaries for ongoing Zoom or Google Meet calls by capturing audio + periodic screenshots
2. Voice triggered automations that launch apps/websites or sequences of actions. It's still in beta right now, but the idea is to be able to automate repetitive flows with this.

Yes, it's an electron app. We are building this for fun on the side from our day job. The overhead of writing two different apps for different platforms is a lot of effort honestly. So we decided to go with Electron. I know, it's not optimal in terms of the size, right now the DMG stands at ~120mb.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": ["Vowen", "Spokenly", "FluidVoice"],
  "sentiment_score": null,
  "complaints": []
}
```

**Why this output?**
- Sentiment is **null** because this comment is about Vowen, not about Wispr Flow
- Competitors mentioned: Vowen, Spokenly, FluidVoice
- No complaints extracted because the comment doesn't discuss Wispr Flow
- Even though thread mentions "alternative to Wispr Flow" in title, the TARGET comment only discusses Vowen features

---

### Example 5: Using Context to Enrich Vague Complaints

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: How to dictate without formatting?
Body: Hi guys! Is there a way I can dictate and use Wispr Flow without formatting? The issue is that for some cases, I will have to just dictate the text in one box, and I don't want to separate it or format it in any way. Unfortunately, I wasn't able to turn it off, so is there a solution for this?

    [COMMENT - CONTEXT]
    Hey u/RaidenHUN, u/Turbulent-Apple2911 this is a setting you can toggle off.

    For a detailed explanation of what Smart Formatting entails, you can also check this help page: https://docs.wisprflow.ai/articles/5883868291-smart-formatting-backtrack
```

**TARGET COMMENT:**

```
I don't quite understand. How do I toggle it?
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": null,
  "complaints": [
    {
      "complaint": "Unclear how to disable Smart Formatting",
      "quote": "I don't quite understand. How do I toggle it?"
    }
  ]
}
```

**Why this output?**
- Sentiment is **null** - neutral question asking for help
- Complaint extracted: "Unclear how to disable Smart Formatting" (NOT just "Unclear how to toggle setting")
- Used thread context to identify that "it" refers to "Smart Formatting" feature
- Enriched the complaint with specific feature name to make it understandable standalone
- Quote is from TARGET comment (as required)

---

### Example 6: Support Response (No Sentiment)

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Best dictation settings?
Body: What are the recommended settings for dictation accuracy?
```

**TARGET COMMENT:**

```
Hey! You can find detailed settings information in our help docs at https://docs.wisprflow.ai/settings
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": null,
  "complaints": []
}
```

**Why this output?**
- Sentiment is **null** because this is a purely informational support response
- No opinion or feeling is expressed - just factual help
- This is a how-to answer, not a review or sentiment
- No complaints in the TARGET comment

---

### Example 7: Aggressive Deduplication (Multiple Mentions of Same Issue)

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: AI Formatting Feature Request
Body: It would be great to have more control over the formatting features.
```

**TARGET COMMENT:**

```
I have previously criticized on Slack and here on Reddit that the forced AI formatting makes the application unusable for work, because the editing effort is far too high.

It is repeatedly promised that forced AI formatting will include an option to turn it off. But for weeks and months, nothing has happened. This has led me to increasingly switch to other speech-to-text applications, and I barely use this one anymore. If the situation does not improve, I will not extend my Pro subscription.
```

**CORRECT OUTPUT:**

```json
{
  "competitors_mentioned": [],
  "sentiment_score": 1,
  "complaints": [
    {
      "complaint": "Cannot disable AI formatting",
      "quote": "the forced AI formatting makes the application unusable for work, because the editing effort is far too high."
    }
  ]
}
```

**Why this output?**
- Sentiment is 1 (very negative) - "unusable", switching to competitors, won't renew subscription
- **Only ONE complaint** even though formatting is mentioned multiple times:
  - "forced AI formatting makes the application unusable" = about AI formatting
  - "no option to turn it off" = about AI formatting
  - Both are the SAME CORE ISSUE → Combined into "Cannot disable AI formatting"
- Chose the first quote as it's most representative of the actual impact
- ❌ WRONG would be to extract 2 separate complaints for "forced formatting" and "can't turn off"

---

## Now Extract Insights from This Thread:

[THREAD WILL BE PROVIDED HERE]
