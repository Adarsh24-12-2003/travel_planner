from __future__ import annotations
from typing import Dict, Any, List
from datetime import date, timedelta
import random

from .config import CONFIG

# ---- Offline datasets (simple + deterministic) ----
AIRPORTS = {
    "mumbai": "BOM",
    "goa": "GOI",
    "delhi": "DEL",
    "bangalore": "BLR",
    "hyderabad": "HYD",
    "pune": "PNQ",
}

def _maybe_fail_transiently():
    if not CONFIG.SIMULATE_TRANSIENT_FAILURES:
        return
    if random.random() < CONFIG.TRANSIENT_FAILURE_RATE:
        # transient errors: retryable
        raise TimeoutError("Simulated transient timeout in tool call.")

def flight_search(origin: str, destination: str, start_date: date, budget_inr: int) -> Dict[str, Any]:
    _maybe_fail_transiently()
    o = AIRPORTS.get(origin.lower(), origin[:3].upper())
    d = AIRPORTS.get(destination.lower(), destination[:3].upper())
    # Fake price bands based on budget
    base = max(2500, min(18000, budget_inr // 10))
    options = [
        {"carrier": "IndiGo", "from": o, "to": d, "date": str(start_date), "price_inr": base},
        {"carrier": "Air India", "from": o, "to": d, "date": str(start_date), "price_inr": int(base * 1.2)},
    ]
    return {"options": options}

def hotel_search(destination: str, start_date: date, trip_days: int, budget_inr: int) -> Dict[str, Any]:
    _maybe_fail_transiently()
    # allocate 40% budget to hotel
    hotel_budget = int(budget_inr * 0.4)
    per_night = max(1200, hotel_budget // max(1, trip_days))
    options = [
        {"name": "Comfort Stay", "city": destination, "nights": trip_days, "per_night_inr": per_night},
        {"name": "Business Inn", "city": destination, "nights": trip_days, "per_night_inr": int(per_night * 1.3)},
    ]
    return {"options": options}

def local_activities(destination: str) -> Dict[str, Any]:
    # Non-retryable typically (but we keep it simple)
    activities = {
        "goa": ["Baga Beach", "Fort Aguada", "Dolphin cruise", "Spice plantation tour"],
        "delhi": ["Red Fort", "Qutub Minar", "India Gate", "Chandni Chowk food walk"],
    }
    return {"activities": activities.get(destination.lower(), ["City walk", "Local market", "Museum visit"])}

def build_itinerary(destination: str, start_date: date, trip_days: int, activities: List[str]) -> Dict[str, Any]:
    plan = []
    for i in range(trip_days):
        day = start_date + timedelta(days=i)
        pick = activities[i % len(activities)] if activities else "Explore locally"
        plan.append({"day": i + 1, "date": str(day), "highlight": pick})
    return {"itinerary": plan}
