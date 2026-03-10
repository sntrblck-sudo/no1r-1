#!/usr/bin/env python3
"""finance_simulation.py

Purely local, simulated ledger for no1r.

- No real wallets, APIs, or money touched.
- Tracks a toy ledger of jobs, income, and costs (e.g. VPS rent).
- Useful for rehearsing policies and decision logic over time.

State lives in finance_state.json in the workspace.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
from datetime import datetime

from no1r_core import WORKSPACE, now_utc, log, load_json, save_json

STATE_FILE = WORKSPACE / "finance_state.json"


@dataclass
class FinanceState:
    version: int
    last_updated: str
    balance_sim: float
    monthly_vps_cost: float
    jobs_completed: int
    jobs_pending: int
    notes: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinanceState":
        return cls(
            version=int(data.get("version", 1)),
            last_updated=str(data.get("last_updated", now_utc().isoformat() + "Z")),
            balance_sim=float(data.get("balance_sim", 0.0)),
            monthly_vps_cost=float(data.get("monthly_vps_cost", 5.0)),
            jobs_completed=int(data.get("jobs_completed", 0)),
            jobs_pending=int(data.get("jobs_pending", 0)),
            notes=str(data.get("notes", "simulation only; no real funds")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_state() -> FinanceState:
    raw = load_json(STATE_FILE, default=None)
    if not raw:
        return FinanceState(
            version=1,
            last_updated=now_utc().isoformat() + "Z",
            balance_sim=0.0,
            monthly_vps_cost=5.0,
            jobs_completed=0,
            jobs_pending=0,
            notes="simulation only; no real funds",
        )
    return FinanceState.from_dict(raw)


def save_state(state: FinanceState) -> None:
    state.last_updated = now_utc().isoformat() + "Z"
    save_json(STATE_FILE, state.to_dict())


def simulate_tick(state: FinanceState) -> FinanceState:
    """Advance the simulation by one tick.

    For now, keep it minimal:
    - Assume no new jobs by default.
    - If balance_sim < monthly_vps_cost, note that we could not cover cost.
    - If balance_sim >= monthly_vps_cost, simulate paying rent.
    """

    log("Running finance simulation tick (purely simulated)", scope="finance")

    if state.balance_sim >= state.monthly_vps_cost:
        state.balance_sim -= state.monthly_vps_cost
        state.notes = "simulated: VPS rent covered this tick."
    else:
        state.notes = "simulated: insufficient balance to cover VPS rent this tick."

    return state


def main() -> None:
    state = load_state()
    state = simulate_tick(state)
    save_state(state)

    # Print a short summary for humans
    print("Finance Simulation (sim only)")
    print(f"- Balance (sim): ${state.balance_sim:.2f}")
    print(f"- Monthly VPS cost (sim): ${state.monthly_vps_cost:.2f}")
    print(f"- Jobs completed (sim): {state.jobs_completed}")
    print(f"- Jobs pending (sim): {state.jobs_pending}")
    print(f"- Last note: {state.notes}")


if __name__ == "__main__":
    main()
