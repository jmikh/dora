# Common Rules for Value Driver Extraction

## What is Wispr Flow?

Wispr Flow is a voice dictation app that lets users write by speaking instead of typing.

## What are Value Drivers?

Value drivers are the **reasons WHY users love the product** - the benefits, advantages, and positive outcomes they experience.

**CRITICAL DISTINCTION:**
- **Use cases** = WHAT users do with Wispr (emails, coding, notes)
- **Value drivers** = WHY users love Wispr (speed, accuracy, convenience)

## PREDEFINED VALUE DRIVER CATEGORIES

You MUST classify each value driver into one of these predefined categories:

| Category | Description | Examples |
|----------|-------------|----------|
| `productivity` | Getting work done faster, time savings | "4x faster than typing", "get more done", "saves hours" |
| `speed` | Fast transcription, low latency | "transcribes instantly", "no delay", "real-time", "keeps up with my speech" |
| `accuracy` | Quality of transcription | "gets every word right", "no typos", "accurate even with technical terms" |
| `reliability` | Consistent performance | "works every time", "never crashes", "dependable", "stable" |
| `ease_of_use` | Simple, intuitive experience | "easy to set up", "just works", "intuitive", "simple UX", "no learning curve" |
| `accessibility` | Helps with physical/speech conditions | "helps with my stutter", "no more wrist pain", "arthritis relief", "understands my accent" |
| `formatting` | Auto-formatting capabilities | "adds punctuation", "capitalizes properly", "creates lists", "formats paragraphs" |
| `contextual_understanding` | Understands intent, not just words | "knows what I mean", "cleans up my rambling", "writes what I intended", "captures intent" |
| `universality` | Works everywhere | "works in every app", "use it anywhere", "universal compatibility" |
| `other` | Anything that doesn't fit above | Specify what it is |

## CRITICAL RULES

1. Extract value drivers ONLY about **Wispr Flow** from the content
2. Each value driver MUST map to one of the predefined categories above
3. If it doesn't fit any category, use `other` and specify what it is
4. Only extract from genuinely positive statements (not sarcasm)
5. Focus on WHY they love it, not WHAT they use it for (that's use cases)
6. **EACH CATEGORY CAN ONLY APPEAR ONCE** - if multiple quotes support the same category, pick the best/most representative quote

## What is NOT a Value Driver

- Use cases: "I use it for emails" (that's WHAT, not WHY)
- Feature names without benefit: "It has a dictionary"
- Generic praise: "It's great", "I love it" (no specific benefit)
- Comparisons without benefit: "Better than Siri" (why is it better?)
