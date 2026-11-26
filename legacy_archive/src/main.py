from __future__ import annotations
import argparse
from datetime import date
from .state import TravelRequest, AgentState, ensure_state
from .graph import build_graph

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="origin", required=True)
    p.add_argument("--to", dest="destination", required=True)
    p.add_argument("--start", dest="start_date", required=True, help="YYYY-MM-DD")
    p.add_argument("--days", dest="trip_days", type=int, required=True)
    p.add_argument("--budget_inr", type=int, required=True)
    p.add_argument("--prefs", nargs="*", default=[])
    return p.parse_args()

def main():
    args = parse_args()
    req = TravelRequest(
        origin=args.origin,
        destination=args.destination,
        start_date=date.fromisoformat(args.start_date),
        trip_days=args.trip_days,
        budget_inr=args.budget_inr,
        preferences=args.prefs,
    )
    state = AgentState(request=req)
    app = build_graph()
    out = ensure_state(app.invoke(state))

    # Pretty print
    import json
    print(json.dumps(out.final_plan, indent=2, default=str))

    if out.errors:
        print("\n--- Notes / errors captured during run ---")
        for e in out.errors:
            print("-", e)

if __name__ == "__main__":
    main()
