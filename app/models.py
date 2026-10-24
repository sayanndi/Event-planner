"""Pydantic models shared by the API and the planning engine.

Every field that comes from a user is bounded (length, range, pattern) so bad
input is rejected at the edge, before it reaches any business logic or the LLM.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

MAX_GUESTS = 5_000
MAX_BUDGET = 1_000_000_000

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class EventType(str, Enum):
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    COMMUNITY = "community"


class PlanRequest(BaseModel):
    """What the user tells us about their event."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_type: EventType
    title: str = Field(min_length=1, max_length=80)
    event_date: date
    guest_count: int = Field(ge=1, le=MAX_GUESTS)
    total_budget: float = Field(ge=1, le=MAX_BUDGET, allow_inf_nan=False)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    location: str = Field(default="", max_length=80)
    preferences: str = Field(default="", max_length=500)

    @field_validator("event_date")
    @classmethod
    def _must_be_in_future(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("must be a date after today")
        return value


class BudgetLine(BaseModel):
    category: str
    percent: int
    amount: float
    per_guest: float


class Milestone(BaseModel):
    id: str
    title: str
    category: str
    due_date: date
    days_before_event: int


class VendorChecklist(BaseModel):
    category: str
    priority: Literal["high", "medium", "low"]
    book_by: date
    questions: list[str]


class IdeaSet(BaseModel):
    """Personalised ideas. ``extra='ignore'`` drops anything unexpected an LLM adds."""

    model_config = ConfigDict(extra="ignore")

    themes: list[ShortText] = Field(min_length=1, max_length=6)
    activities: list[ShortText] = Field(min_length=1, max_length=6)
    menu: list[ShortText] = Field(min_length=1, max_length=6)
    tips: list[ShortText] = Field(min_length=1, max_length=6)
    source: Literal["ai", "offline"] = "offline"


class PlanSummary(BaseModel):
    days_until_event: int
    budget_per_guest: float
    warnings: list[str]


class EventPlan(BaseModel):
    request: PlanRequest
    summary: PlanSummary
    budget: list[BudgetLine]
    timeline: list[Milestone]
    vendors: list[VendorChecklist]
    ideas: IdeaSet
