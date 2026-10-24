"""Static planning knowledge: budget splits, milestones and vendor questions.

Keeping data apart from logic means a planner (or a translator) can improve the
advice without touching any code, and tests can check the data for consistency.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models import EventType


@dataclass(frozen=True)
class MilestoneTemplate:
    days_before: int
    title: str
    category: str


@dataclass(frozen=True)
class VendorTemplate:
    category: str
    priority: str  # "high" | "medium" | "low"
    days_before: int
    questions: tuple[str, ...]


@dataclass(frozen=True)
class Blueprint:
    horizon_days: int  # the longest lead time the templates assume
    min_recommended_days: int  # below this we warn that time is tight
    budget_split: dict[str, int]  # category -> whole percent, must total 100
    milestones: tuple[MilestoneTemplate, ...]  # ordered from earliest to latest
    vendors: tuple[VendorTemplate, ...]


_COMMON_QUESTIONS = (
    "What is the total price, and what exactly is included?",
    "What is the deposit, and what is the cancellation and refund policy?",
)

WEDDING = Blueprint(
    horizon_days=270,
    min_recommended_days=180,
    budget_split={
        "Venue": 25,
        "Catering": 33,
        "Decor & Flowers": 10,
        "Photography & Video": 10,
        "Attire & Beauty": 8,
        "Music & Entertainment": 5,
        "Invitations & Misc": 4,
        "Contingency": 5,
    },
    milestones=(
        MilestoneTemplate(270, "Agree the budget and draft the guest list", "Planning"),
        MilestoneTemplate(240, "Shortlist and book the venue", "Booking"),
        MilestoneTemplate(180, "Book caterer and photographer", "Booking"),
        MilestoneTemplate(150, "Send save-the-date messages", "Guests"),
        MilestoneTemplate(120, "Choose attire and book decorator", "Booking"),
        MilestoneTemplate(90, "Finalise menu, music and ceremony schedule", "Planning"),
        MilestoneTemplate(60, "Send formal invitations", "Guests"),
        MilestoneTemplate(45, "Hair and makeup trial", "Final prep"),
        MilestoneTemplate(30, "Collect RSVPs and confirm headcount", "Guests"),
        MilestoneTemplate(14, "Confirm every vendor and settle payment schedule", "Logistics"),
        MilestoneTemplate(7, "Finish seating plan and run a rehearsal", "Final prep"),
        MilestoneTemplate(1, "Assign day-of helpers and pack an emergency kit", "Final prep"),
    ),
    vendors=(
        VendorTemplate("Venue", "high", 240, (
            *_COMMON_QUESTIONS,
            "What is the maximum capacity and is there a backup for bad weather?",
            "Are outside caterers and decorators allowed? Is there a corkage or setup fee?",
        )),
        VendorTemplate("Caterer", "high", 180, (
            *_COMMON_QUESTIONS,
            "Can you arrange a tasting and cater to dietary needs (vegetarian, vegan, allergies)?",
            "How many staff will serve, and how is leftover food handled?",
        )),
        VendorTemplate("Photographer & Videographer", "high", 180, (
            *_COMMON_QUESTIONS,
            "How many hours, how many photographers, and when are edited photos delivered?",
        )),
        VendorTemplate("Decorator & Florist", "medium", 120, (
            *_COMMON_QUESTIONS,
            "Can you share photos of past work and a 3D or sketch plan of our space?",
        )),
        VendorTemplate("Attire, Makeup & Hair", "medium", 120, (
            *_COMMON_QUESTIONS,
            "How many fittings or trials are included and what is the alteration timeline?",
        )),
        VendorTemplate("Music, DJ or Band", "medium", 90, (
            *_COMMON_QUESTIONS,
            "Do you bring your own sound system, and what is the overtime rate?",
        )),
        VendorTemplate("Invitations & Printing", "low", 75, (
            "What is the turnaround time and is a proof provided before printing?",
            "What is the price per piece at our guest count?",
        )),
        VendorTemplate("Guest Transport", "low", 30, (
            *_COMMON_QUESTIONS,
            "Are drivers and vehicles available on the day without extra charges?",
        )),
    ),
)

BIRTHDAY = Blueprint(
    horizon_days=42,
    min_recommended_days=21,
    budget_split={
        "Venue": 20,
        "Food & Cake": 40,
        "Decor & Balloons": 12,
        "Entertainment": 13,
        "Invitations & Return Gifts": 5,
        "Photography": 3,
        "Contingency": 7,
    },
    milestones=(
        MilestoneTemplate(42, "Set the budget, theme and guest list", "Planning"),
        MilestoneTemplate(35, "Book the venue or confirm the home setup", "Booking"),
        MilestoneTemplate(28, "Design and order invitations", "Guests"),
        MilestoneTemplate(21, "Send invitations", "Guests"),
        MilestoneTemplate(14, "Order the cake and book entertainment", "Booking"),
        MilestoneTemplate(7, "Confirm RSVPs and buy supplies and return gifts", "Guests"),
        MilestoneTemplate(3, "Reconfirm every vendor and delivery time", "Logistics"),
        MilestoneTemplate(1, "Set up decor and prepare the schedule of activities", "Final prep"),
    ),
    vendors=(
        VendorTemplate("Venue", "medium", 35, (
            *_COMMON_QUESTIONS,
            "Is there a time limit, and are decorations and outside food allowed?",
        )),
        VendorTemplate("Cake & Bakery", "high", 14, (
            "Can the cake meet allergy or eggless requirements?",
            "How and when is it delivered, and what keeps it safe in hot weather?",
        )),
        VendorTemplate("Caterer", "medium", 21, (
            *_COMMON_QUESTIONS,
            "Do you offer a kids' menu and portion estimates for our headcount?",
        )),
        VendorTemplate("Entertainer or Host", "medium", 21, (
            *_COMMON_QUESTIONS,
            "What age range suits your show and how long does it run?",
        )),
        VendorTemplate("Decor & Balloons", "low", 14, (
            "Is setup and clean-up included and how early can you arrive?",
        )),
        VendorTemplate("Photographer", "low", 14, (
            "How many hours are covered and how are photos shared?",
        )),
    ),
)

COMMUNITY = Blueprint(
    horizon_days=84,
    min_recommended_days=42,
    budget_split={
        "Venue & Permits": 20,
        "Food & Refreshments": 30,
        "Sound, Stage & AV": 15,
        "Publicity & Printing": 10,
        "Volunteers & Supplies": 10,
        "Safety & First Aid": 5,
        "Contingency": 10,
    },
    milestones=(
        MilestoneTemplate(84, "Define the purpose, audience and organising committee", "Planning"),
        MilestoneTemplate(70, "Apply for permissions and permits", "Booking"),
        MilestoneTemplate(56, "Book the venue and sound equipment", "Booking"),
        MilestoneTemplate(42, "Recruit volunteers and assign roles", "Planning"),
        MilestoneTemplate(35, "Launch publicity and approach sponsors", "Guests"),
        MilestoneTemplate(28, "Finalise the programme and schedule", "Planning"),
        MilestoneTemplate(14, "Finish the safety, first-aid and crowd plan", "Logistics"),
        MilestoneTemplate(7, "Brief volunteers and confirm every vendor", "Logistics"),
        MilestoneTemplate(1, "Set up the venue and run a logistics check", "Final prep"),
    ),
    vendors=(
        VendorTemplate("Venue or Ground Owner", "high", 70, (
            *_COMMON_QUESTIONS,
            "Which permissions are needed and who applies for them?",
            "Are there rules about noise, closing time and clean-up?",
        )),
        VendorTemplate("Sound, Stage & Lighting", "high", 56, (
            *_COMMON_QUESTIONS,
            "Is power backup included and who is on site during the event?",
        )),
        VendorTemplate("Safety & First Aid", "high", 21, (
            "How many trained people do you provide for our crowd size?",
            "What is the plan for emergencies and how do we contact local services?",
        )),
        VendorTemplate("Food & Refreshments", "medium", 35, (
            *_COMMON_QUESTIONS,
            "Do you hold a valid food-safety licence and offer inclusive options?",
        )),
        VendorTemplate("Printing & Banners", "medium", 28, (
            "What is the turnaround time and is a proof provided?",
        )),
        VendorTemplate("Furniture & Equipment Rental", "low", 28, (
            *_COMMON_QUESTIONS,
            "Who handles delivery, setup and collection?",
        )),
    ),
)

BLUEPRINTS: dict[EventType, Blueprint] = {
    EventType.WEDDING: WEDDING,
    EventType.BIRTHDAY: BIRTHDAY,
    EventType.COMMUNITY: COMMUNITY,
}
