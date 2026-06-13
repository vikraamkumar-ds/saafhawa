"""
Shared data contracts. THIS IS THE FROZEN JSON CONTRACT (Day 1 lock).
Owner B builds the frontend against PlanResponse / AqiResponse / AskResponse.
Do not rename fields without telling the other owner.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Household profile flags that change the advice
class Household(BaseModel):
    child: bool = False
    elderly: bool = False
    pregnant: bool = False
    allergies: bool = False          # pollen / environmental
    heart_lung: bool = False
    outdoor_worker: bool = False

    def descriptors(self) -> List[str]:
        labels = {
            "child": "young child",
            "elderly": "elderly member",
            "pregnant": "pregnant person",
            "allergies": "pollen/environmental allergies",
            "heart_lung": "heart or lung condition",
            "outdoor_worker": "outdoor worker",
        }
        return [labels[k] for k, v in self.model_dump().items() if v]


class AqiResponse(BaseModel):
    area: str
    aqi: int
    category: str            # honest health category
    dominant_pollutant: Optional[str] = None
    station: Optional[str] = None
    updated: Optional[str] = None
    source: Literal["waqi", "openweather", "fallback"] = "waqi"
    stale: bool = False      # True if served while live source was down


class PlanRequest(BaseModel):
    area: str = "lahore"
    household: Household = Field(default_factory=Household)


class PlanResponse(BaseModel):
    area: str
    aqi: int
    category: str
    verdict_en: str          # one-line verdict
    verdict_ur: str
    steps_en: List[str]      # 3-4 concrete steps
    steps_ur: List[str]
    why_en: str              # short reason
    why_ur: str
    source: str = "ai"       # "ai" or "fallback"


class AskRequest(BaseModel):
    area: str = "lahore"
    household: Household = Field(default_factory=Household)
    question: str


class AskResponse(BaseModel):
    answer_en: str
    answer_ur: str
    aqi: int
    category: str
    source: str = "ai"
