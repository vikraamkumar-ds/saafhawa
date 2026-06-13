<div align="center">

# SaafHawa 🌫️ → ✅
### صاف ہوا

**Air-quality data, turned into a decision you can act on — in your language.**

![Built with FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)
![AI](https://img.shields.io/badge/AI-Groq%20·%20Llama%203.3%2070B-F4A23B)
![Bilingual](https://img.shields.io/badge/EN%20+%20اردو-bilingual-16B6D4)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

SaafHawa is an AI layer on top of public air-quality data. Instead of showing a
number, it asks who's in your home and turns today's local AQI into specific,
plain-language action — in **English and Urdu** — plus a chat that answers
everyday questions like *"is it safe to walk to school this morning?"*

Built for caregivers in air-sensitive households across **Lahore, Karachi & Islamabad** —
families with young children, elderly members, pregnant members, or people with
pollen, asthma, heart/lung conditions.

> Submitted to the **AI for Civic Innovation Hackathon 2026** (Code for Pakistan ×
> Grey Software × Scrimba × FAST NUCES Islamabad).
> **Themes:** Technology for Civic Good · Open Data & Access to Information.

---

## ✨ Features

- 📍 **Area-level AQI** for Lahore, Karachi & Islamabad with honest US-EPA health categories
- 👨‍👩‍👧 **Household profiles** — child · elderly · pregnant · allergies · heart/lung · outdoor worker — each changes the advice
- 🤖 **Live AI action plan** — one-line verdict + 3–4 concrete steps + why
- 🌐 **Bilingual by default** — every output in English **and** Urdu (Nastaliq)
- 💬 **Ask-anything chat** — grounded in your air level and household
- 🛟 **Offline-safe** — graceful fallback so guidance always loads, even if APIs are down

## 🏗️ Architecture

```
Browser / Telegram  →  FastAPI backend  →  WAQI air data  ┐
                          /aqi /plan /ask                 ├→ SQLite cache
                                 ↓                         ┘
                       Groq · Llama 3.3 70B  →  bilingual verdict JSON (EN + اردو)
```

Three endpoints, one frozen JSON contract (see `backend/models.py`), with a
deterministic fallback at every hop so a demo never blanks.

Full diagram: [`assets/architecture.png`](assets/architecture.png) · Request flow: [`assets/workflow.png`](assets/workflow.png)

## 🚀 Quick start

> Tested on Python 3.10 – 3.13 (Windows, macOS, Linux).

```bash
git clone https://github.com/<your-handle>/saafhawa.git
cd saafhawa/backend

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
copy .env.example .env       # macOS/Linux: cp .env.example .env
python -m uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for live, clickable API docs.

> **No tokens yet? It still runs.** `/aqi` serves an offline estimate and `/plan`
> + `/ask` use a deterministic bilingual fallback — so the frontend always renders.

### Free tokens (no card)
| Service | Where | Used for |
|---|---|---|
| WAQI / aqicn | https://aqicn.org/data-platform/token/ | real station AQI |
| Groq (Llama 3.3 70B) | https://console.groq.com/keys | bilingual AI interpretation |
| OpenWeather *(optional)* | https://openweathermap.org/api/air-pollution | fallback air source |

Paste the keys into `backend/.env`, then restart uvicorn.

## 📡 API

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/aqi?area=lahore` | – | `AqiResponse` |
| `POST` | `/plan` | `{ area, household }` | `PlanResponse` |
| `POST` | `/ask` | `{ area, household, question }` | `AskResponse` |

`household` flags (all optional, default `false`): `child` · `elderly` · `pregnant` · `allergies` · `heart_lung` · `outdoor_worker`.

**Try it**
```bash
curl -X POST http://localhost:8000/plan ^
  -H "Content-Type: application/json" ^
  -d "{\"area\":\"lahore\",\"household\":{\"child\":true,\"allergies\":true}}"
```

<details>
<summary>Sample response</summary>

```json
{
  "area": "lahore",
  "aqi": 168,
  "category": "Unhealthy",
  "verdict_en": "Keep your child indoors until noon.",
  "verdict_ur": "بچے کو دوپہر تک گھر کے اندر رکھیں۔",
  "steps_en": ["Close windows during peak hours", "Mask the school run", "Rinse off pollen after coming inside"],
  "steps_ur": ["صبح و شام کھڑکیاں بند رکھیں", "اسکول جاتے وقت ماسک پہنائیں", "اندر آنے کے بعد چہرہ دھوئیں"],
  "why_en": "Sensitive members react to fine particles well before healthy adults feel anything.",
  "why_ur": "باریک ذرات صحت مند بالغ سے پہلے حساس افراد کو متاثر کرتے ہیں۔",
  "source": "ai"
}
```

</details>

## 🧠 The AI part

Groq's Llama 3.3 70B (OpenAI-compatible API) interprets the AQI in context of a
specific household and emits a strict bilingual verdict JSON. Why AI fits here:
turning a number into safe, *personalized*, *plain-language* advice — in two
languages, including natural Urdu — is a reasoning + NLG problem that rules
can't cover at the needed nuance and fluency. If the LLM is unreachable, a
deterministic rule-based plan still returns useful bilingual guidance — so the
service degrades gracefully and never goes blank.

## 📁 Project structure

```
saafhawa/
├── backend/
│   ├── main.py           # FastAPI app — /aqi /plan /ask
│   ├── aqi.py            # WAQI → OpenWeather → last-good fallback
│   ├── llm.py            # Groq Llama 3.3 70B + deterministic fallback
│   ├── cache.py          # SQLite TTL + last-good store
│   ├── config.py         # env / tokens / area mapping
│   ├── models.py         # 🔒 frozen JSON contract (Pydantic)
│   ├── requirements.txt
│   └── .env.example
├── assets/               # architecture, workflow, thumbnails, cover
├── HANDOFF_OwnerB.md     # frontend / UX / submission guide
├── SUBMISSION.md         # paste-ready Devpost text (all 6 reqs)
├── SaafHawa_Pitch.pptx   # pitch deck
└── README.md
```

## 🗺️ Roadmap

Live low-cost sensor integration · WhatsApp / SMS delivery · next-day forecast ·
more cities · additional local languages.

## 💡 Inspiration

Pakistan's cities sit near the top of every "most polluted air" list in the world,
and the people who pay the price are the ones least equipped to read the data —
parents deciding on a school run, an elderly relative breathing through a smoggy
morning, a pregnant woman, a delivery rider working outdoors all day, anyone with
asthma or pollen allergy.

Public AQI data already exists. The gap isn't measurement — it's *interpretation*.
Today the answer to "is the air safe for my child right now?" is a three-digit
number and a color, in English, with no idea what to actually do. SaafHawa closes
that last mile: it takes the open data citizens already pay for and turns it into
a clear, personal, bilingual decision — what to do, why it matters, in the
language people actually think in.

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**SaafHawa · صاف ہوا**
Made with ❤️ for the people who feel the air first.

</div>
