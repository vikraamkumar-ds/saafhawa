"""SaafHawa backend — FastAPI. Three endpoints: /aqi, /plan, /ask.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import aqi as aqi_svc
import cache
import config
import llm
from models import (AqiResponse, AskRequest, AskResponse,
                    PlanRequest, PlanResponse)

app = FastAPI(title="SaafHawa API", version="1.0")

# Frontend runs separately (Vercel/local) — allow it to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "SaafHawa", "areas": list(config.AREAS.keys()),
            "endpoints": ["/aqi", "/plan", "/ask"]}


@app.get("/aqi", response_model=AqiResponse)
async def get_aqi(area: str = config.DEFAULT_AREA):
    """Live area-level AQI + honest health category."""
    return await aqi_svc.get_aqi(area)


@app.post("/plan", response_model=PlanResponse)
async def make_plan(req: PlanRequest):
    """Bilingual action plan: verdict + steps + why, tailored to the household."""
    air = await aqi_svc.get_aqi(req.area)
    ckey = f"plan:{req.area}:{req.household.model_dump_json()}"
    cached = cache.get(ckey)
    if cached:
        return PlanResponse(**cached)
    plan = await llm.make_plan(req.area, air.aqi, air.category, req.household)
    cache.set(ckey, plan.model_dump(), config.PLAN_TTL)
    return plan


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """Ask-anything assistant grounded in today's air level + household."""
    air = await aqi_svc.get_aqi(req.area)
    return await llm.make_answer(req.area, air.aqi, air.category,
                                 req.household, req.question)
