from __future__ import annotations
from typing import Dict, Any
from langchain_core.messages import HumanMessage

from .state import AgentState, Critique
from .tools import flight_search, hotel_search, local_activities, build_itinerary
from .retry import RetryPolicy, with_retries
from .guards import safe_call, GuardError
from .config import CONFIG
from .llm import get_llm

def _log(state: AgentState, msg: str):
    # lightweight logging for workshops
    state.errors.append(msg)

def research_node(state: AgentState) -> AgentState:
    req = state.request
    policy = RetryPolicy(
        max_retries=CONFIG.MAX_RETRIES,
        base_seconds=CONFIG.BACKOFF_BASE_SECONDS,
        max_seconds=CONFIG.BACKOFF_MAX_SECONDS,
        retry_on=(TimeoutError, ConnectionError),
    )

    def do_flights():
        return flight_search(req.origin, req.destination, req.start_date, req.budget_inr)

    def do_hotels():
        return hotel_search(req.destination, req.start_date, req.trip_days, req.budget_inr)

    try:
        flights = safe_call("flight_search", with_retries(do_flights, policy))
        hotels  = safe_call("hotel_search", with_retries(do_hotels, policy))
        acts    = safe_call("local_activities", lambda: local_activities(req.destination))
        state.research = {"flights": flights, "hotels": hotels, "activities": acts}
        state.last_failed_step = None
        return state
    except GuardError as ge:
        state.last_failed_step = "research"
        _log(state, str(ge))
        return state

def plan_node(state: AgentState) -> AgentState:
    req = state.request
    if not state.research:
        state.last_failed_step = "plan"
        _log(state, "[plan] missing research; cannot plan.")
        return state

    flights = state.research.get("flights", {}).get("options", [])
    hotels = state.research.get("hotels", {}).get("options", [])
    activities = state.research.get("activities", {}).get("activities", [])

    itinerary = safe_call("build_itinerary", lambda: build_itinerary(req.destination, req.start_date, req.trip_days, activities))

    # Keep as structured plan (Session 18 focuses robustness, not fancy generation)
    state.draft_plan = {
        "summary": {
            "from": req.origin,
            "to": req.destination,
            "start": str(req.start_date),
            "days": req.trip_days,
            "budget_inr": req.budget_inr,
        },
        "flight_options": flights,
        "hotel_options": hotels,
        "itinerary": itinerary["itinerary"],
    }
    state.last_failed_step = None
    return state

def critique_node(state: AgentState) -> AgentState:
    if not state.draft_plan:
        state.last_failed_step = "critique"
        _log(state, "[critique] missing draft_plan.")
        return state

    llm = get_llm()

    prompt = f"""You are a travel plan reviewer.
Rate the plan from 0-10 (integer). Return JSON with keys: score, issues (list), suggested_fixes (list).

Plan JSON:
{state.draft_plan}
"""

    try:
        msg = llm.invoke([HumanMessage(content=prompt)])
        text = msg.content if hasattr(msg, "content") else str(msg)

        # Guard: extract a JSON-ish object. If parsing fails, degrade gracefully.
        import json, re
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            # fallback critique (no crash)
            state.critique = Critique(score=6, issues=["Could not parse critique JSON."], suggested_fixes=["Keep plan concise; verify totals."])
            return state
        data = json.loads(m.group(0))
        state.critique = Critique.model_validate(data)
        state.last_failed_step = None
        return state
    except Exception as e:
        state.last_failed_step = "critique"
        _log(state, f"[critique] failed: {e}")
        # fallback critique
        state.critique = Critique(score=6, issues=["LLM critique unavailable."], suggested_fixes=["Add more details; verify budget."])
        return state

def revise_node(state: AgentState) -> AgentState:
    # Simple “revision”: if issues mention budget, reduce hotel option; else keep as is.
    if not state.draft_plan or not state.critique:
        state.last_failed_step = "revise"
        _log(state, "[revise] missing draft_plan or critique.")
        return state

    plan = state.draft_plan
    crit = state.critique

    if any("budget" in x.lower() for x in crit.issues):
        # guard: ensure list exists
        hotels = plan.get("hotel_options") or []
        if hotels:
            hotels = sorted(hotels, key=lambda h: h.get("per_night_inr", 10**9))
            plan["hotel_options"] = hotels[:1]

    state.draft_plan = plan
    state.revisions_done += 1
    state.last_failed_step = None
    return state

def finalize_node(state: AgentState) -> AgentState:
    # Promote draft to final
    if state.draft_plan:
        state.final_plan = state.draft_plan
    return state

def fallback_node(state: AgentState) -> AgentState:
    # When research fails, still return a minimal safe plan.
    req = state.request
    state.final_plan = {
        "summary": {
            "from": req.origin,
            "to": req.destination,
            "start": str(req.start_date),
            "days": req.trip_days,
            "budget_inr": req.budget_inr,
        },
        "note": "Some tools failed; returning an approximate plan. Try again later for live options.",
        "itinerary": build_itinerary(req.destination, req.start_date, req.trip_days, ["Local sightseeing"])["itinerary"],
    }
    return state
