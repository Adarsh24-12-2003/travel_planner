from __future__ import annotations
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import research_node, plan_node, critique_node, revise_node, finalize_node, fallback_node
from .config import CONFIG

def should_fallback(state: AgentState) -> str:
    # If research failed, route to fallback
    if state.last_failed_step == "research":
        return "fallback"
    return "plan"

def should_revise_or_finalize(state: AgentState) -> str:
    # If critique missing or low score and we still have revision budget → revise; else finalize
    if state.critique is None:
        return "finalize"
    if state.critique.score < CONFIG.CRITIQUE_PASS_SCORE and state.revisions_done < CONFIG.MAX_REVISIONS:
        return "revise"
    return "finalize"

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("research", research_node)
    g.add_node("fallback", fallback_node)
    g.add_node("plan", plan_node)
    g.add_node("critique", critique_node)
    g.add_node("revise", revise_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("research")

    g.add_conditional_edges("research", should_fallback, {
        "fallback": "fallback",
        "plan": "plan",
    })

    g.add_edge("fallback", "finalize")  # fallback still finalizes

    g.add_edge("plan", "critique")

    g.add_conditional_edges("critique", should_revise_or_finalize, {
        "revise": "revise",
        "finalize": "finalize",
    })

    g.add_edge("revise", "critique")
    g.add_edge("finalize", END)

    return g.compile()
