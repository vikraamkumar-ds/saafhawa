"""LLM interpretation layer (Groq / Llama 3.3 70B, OpenAI-compatible).

Produces the bilingual verdict JSON. Includes a deterministic, rule-based
fallback so /plan and /ask still return useful guidance when the LLM is
unreachable (rate-limited, offline, or no key set)."""
import json
import httpx
import config
from models import Household, PlanResponse, AskResponse

_PLAN_SYSTEM = """You are SaafHawa, an air-quality health assistant for Pakistan.
You turn an AQI number into a clear daily decision for a specific household.
Be honest about risk, practical, and calm. Use plain language a parent would understand.

You MUST reply with ONLY a valid JSON object, no markdown, no preface, with exactly these keys:
{
 "verdict_en": "one short line: the bottom-line decision",
 "verdict_ur": "same verdict in natural Urdu (Nastaliq script)",
 "steps_en": ["3 to 4 concrete actions for today"],
 "steps_ur": ["same steps in Urdu"],
 "why_en": "one or two sentences: why this matters for THIS household",
 "why_ur": "same reason in Urdu"
}
Tailor everything to the household members listed. If allergies are present,
mention pollen/irritants specifically. Keep each step under 18 words."""

_ASK_SYSTEM = """You are SaafHawa, an air-quality health assistant for Pakistan.
Answer the user's everyday question using today's air level and their household.
Be specific and decisive (e.g. "Yes, but keep it under 20 minutes").
Reply with ONLY valid JSON, no markdown:
{"answer_en": "...", "answer_ur": "... (Urdu/Nastaliq)"}"""


def _context(area: str, aqi: int, category: str, hh: Household) -> str:
    members = ", ".join(hh.descriptors()) or "general adults, no special sensitivities"
    return (f"Area: {area}. Current AQI: {aqi} ({category}). "
            f"Household members: {members}.")


async def _chat(system: str, user: str) -> dict:
    if not config.GROQ_API_KEY:
        raise RuntimeError("no GROQ_API_KEY")
    url = f"{config.GROQ_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    body = {
        "model": config.GROQ_MODEL,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    return json.loads(content)


# ----------------------- deterministic fallback -----------------------
def _fallback_plan(area: str, aqi: int, category: str, hh: Household) -> PlanResponse:
    sensitive = any([hh.child, hh.elderly, hh.pregnant, hh.heart_lung, hh.allergies])
    if aqi <= 50:
        v_en, v_ur = "Air is clean — normal outdoor activity is fine today.", "ہوا صاف ہے — آج باہر کی معمول کی سرگرمی ٹھیک ہے۔"
    elif aqi <= 100:
        v_en, v_ur = "Mostly okay; sensitive members should take it easy outdoors.", "زیادہ تر ٹھیک ہے؛ حساس افراد باہر احتیاط کریں۔"
    elif aqi <= 150:
        v_en = "Unhealthy for sensitive members — limit their time outdoors." if sensitive else "Okay for most, but watch sensitive members."
        v_ur = "حساس افراد کے لیے مضر — باہر وقت محدود رکھیں۔"
    elif aqi <= 200:
        v_en, v_ur = "Unhealthy air — keep everyone's outdoor time short today.", "ہوا مضرِ صحت ہے — آج باہر کا وقت کم رکھیں۔"
    else:
        v_en, v_ur = "Very poor air — stay indoors and keep windows closed.", "ہوا بہت خراب — گھر کے اندر رہیں اور کھڑکیاں بند رکھیں۔"

    steps_en = ["Keep windows closed during peak hours (morning & evening).",
                "Run an air purifier or close off one clean room."]
    steps_ur = ["صبح و شام کھڑکیاں بند رکھیں۔",
                "ایئر پیوریفائر چلائیں یا ایک کمرہ صاف رکھیں۔"]
    if hh.child:
        steps_en.append("Move the school run earlier; have child wear a mask.")
        steps_ur.append("بچے کو ماسک پہنائیں اور اسکول جلدی نکلیں۔")
    if hh.allergies:
        steps_en.append("Rinse face/nose after coming inside to clear pollen.")
        steps_ur.append("اندر آنے کے بعد چہرہ اور ناک دھوئیں۔")
    if not (hh.child or hh.allergies):
        steps_en.append("Postpone outdoor exercise until AQI drops below 100.")
        steps_ur.append("AQI 100 سے کم ہونے تک باہر ورزش مؤخر کریں۔")

    why_en = "Sensitive members react to fine particles well before healthy adults feel anything." if sensitive \
        else "Fine particles build up in the lungs even when the air looks clear."
    why_ur = "باریک ذرات صحت مند بالغ سے پہلے حساس افراد کو متاثر کرتے ہیں۔"
    return PlanResponse(area=area, aqi=aqi, category=category,
                        verdict_en=v_en, verdict_ur=v_ur,
                        steps_en=steps_en[:4], steps_ur=steps_ur[:4],
                        why_en=why_en, why_ur=why_ur, source="fallback")


async def make_plan(area: str, aqi: int, category: str, hh: Household) -> PlanResponse:
    try:
        data = await _chat(_PLAN_SYSTEM, _context(area, aqi, category, hh))
        return PlanResponse(area=area, aqi=aqi, category=category,
                            verdict_en=data["verdict_en"], verdict_ur=data["verdict_ur"],
                            steps_en=data["steps_en"][:4], steps_ur=data["steps_ur"][:4],
                            why_en=data["why_en"], why_ur=data["why_ur"], source="ai")
    except Exception:
        return _fallback_plan(area, aqi, category, hh)


async def make_answer(area: str, aqi: int, category: str, hh: Household, question: str) -> AskResponse:
    try:
        user = _context(area, aqi, category, hh) + f"\nQuestion: {question}"
        data = await _chat(_ASK_SYSTEM, user)
        return AskResponse(answer_en=data["answer_en"], answer_ur=data["answer_ur"],
                           aqi=aqi, category=category, source="ai")
    except Exception:
        plan = _fallback_plan(area, aqi, category, hh)
        return AskResponse(answer_en=plan.verdict_en + " " + plan.steps_en[0],
                           answer_ur=plan.verdict_ur + " " + plan.steps_ur[0],
                           aqi=aqi, category=category, source="fallback")
