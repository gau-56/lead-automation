import json
import os

MODEL = os.getenv("LEADS_MODEL", "claude-sonnet-5-5")

HOT_WORDS = ["urgent", "asap", "today", "this week", "quote", "price", "buy", "book", "ready"]
COLD_WORDS = ["just looking", "maybe later", "curious", "someday", "no rush"]


def fallback_analysis(name, message):
    text = message.lower()
    if any(w in text for w in HOT_WORDS):
        score = "hot"
    elif any(w in text for w in COLD_WORDS):
        score = "cold"
    else:
        score = "warm"
    return {
        "score": score,
        "category": "general enquiry",
        "summary": message[:140],
        "suggested_reply": (
            f"Hi {name}, thanks for getting in touch. "
            "We've received your message and will get back to you shortly."
        ),
    }


def analyze_lead(name, message):
    if not os.getenv("ANTHROPIC_API_KEY"):
        return fallback_analysis(name, message)

    try:
        from anthropic import Anthropic

        client = Anthropic()
        prompt = f"""You are a sales assistant for a small business.
Analyze this new enquiry and reply with ONLY a JSON object with these keys:
"score" (hot, warm, or cold), "category" (2-3 words), "summary" (one sentence),
"suggested_reply" (a friendly 2-3 sentence reply that answers only what was asked
and does not promise prices, discounts or availability).

Enquiry from {name}:
{message}"""
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        if data.get("score") not in ("hot", "warm", "cold"):
            raise ValueError("bad score")
        return data
    except Exception as error:
        print("AI analysis failed, using fallback:", error)
        return fallback_analysis(name, message)