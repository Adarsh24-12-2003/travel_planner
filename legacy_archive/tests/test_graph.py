from datetime import date
from src.state import TravelRequest, AgentState, ensure_state
from src.graph import build_graph
from src import config

def test_graph_returns_final_plan(monkeypatch):
    # Reduce failures for deterministic test
    monkeypatch.setattr(config.CONFIG, "SIMULATE_TRANSIENT_FAILURES", False, raising=False)

    req = TravelRequest(origin="Mumbai", destination="Goa", start_date=date(2026,3,10), trip_days=3, budget_inr=30000)
    state = AgentState(request=req)
    app = build_graph()
    out = ensure_state(app.invoke(state))
    assert out.final_plan is not None
    assert out.final_plan["summary"]["to"].lower() == "goa"
