import json
from clients import groq
from config import LLM_MODEL, UCAR_CONTEXT

def gatekeeper(question: str) -> dict:
    """Decides if the question is relevant to University Carthage."""
    print("\n🛡️  [GATEKEEPER] Evaluating question relevance...")
    try:
        response = groq.chat.completions.create(
            model=LLM_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are the relevance gatekeeper for a UCAR Institutional Intelligence chatbot.
The chatbot helps users navigate UCAR documents, get KPIs, and understand university data.
Your ONLY job is to determine if the user's question is TOPICALLY related to University Carthage (UCAR), its 32 institutions, universities in general, higher education KPIs, or document navigation.

{UCAR_CONTEXT}

CRITICAL RULES:
1. ONLY evaluate TOPIC RELEVANCE. 
2. DO NOT try to answer the question yourself.
3. DO NOT reject a question just because you think the information (like costs or KPIs) is "not publicly available". The internal database might have it.
4. Allow ANY question related to students, budgets, staff, navigation, KPIs, programs, institutions, admissions, etc.

Respond ONLY with valid JSON (no markdown, no extra text):
{{"allowed": true, "reason": "..."}}
or
{{"allowed": false, "reason": "..."}}

Reject ONLY completely unrelated topics like cooking, general politics, movie reviews, or unrelated coding."""
                },
                {"role": "user", "content": question}
            ]
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        status = "✅ ALLOWED" if result["allowed"] else "🚫 BLOCKED"
        print(f"   {status} — {result['reason']}")
        return result
    except Exception as e:
        print(f"    Gatekeeper error: {e}")
        return {"allowed": True, "reason": "Gatekeeper failed – defaulting to allow.", "error": str(e)}
