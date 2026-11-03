"""
Production and inventory planning with linear programming (PuLP).

Plans 12 months of production for a seasonal product, using demand forecast
by a Holt-Winters model, and compares two cost scenarios:

  A. Original costs: backlog penalty (0.50/unit/month) is far below the cost
     of producing a unit (8.00), so the cheapest plan defers demand.
  B. Revised costs and service level: backlog penalty raised above overtime
     cost, and all backlog cleared by the end of the year.

Run:  python production_planning.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pulp

# ---------------------------------------------------------------- inputs
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 12-month demand forecast from the Holt-Winters model (units)
DEMAND = [7845, 8380, 10855, 11586, 11847, 15197,
          12123, 11072, 10791, 9964, 10034, 10717]

COST_REGULAR = 8.00      # per unit, regular production
COST_OVERTIME = 12.00    # per unit, overtime production
COST_HOLDING = 0.17      # per unit held in inventory per month
CAP_REGULAR = 14_500     # units per month
CAP_OVERTIME = 1_450     # units per month
OPENING_INVENTORY = 500
CLOSING_INVENTORY_MIN = 500

SCENARIOS = {
    "A_original": {"backlog_cost": 0.50, "clear_backlog_by_dec": False},
    "B_revised":  {"backlog_cost": 15.00, "clear_backlog_by_dec": True},
}

OUT = Path(__file__).parent / "outputs"


def solve(backlog_cost: float, clear_backlog_by_dec: bool) -> dict:
    """Build and solve the LP; return the plan and total cost."""
    T = range(len(DEMAND))
    m = pulp.LpProblem("production_planning", pulp.LpMinimize)

    P = pulp.LpVariable.dicts("regular", T, lowBound=0, upBound=CAP_REGULAR)
    O = pulp.LpVariable.dicts("overtime", T, lowBound=0, upBound=CAP_OVERTIME)
    I = pulp.LpVariable.dicts("inventory", T, lowBound=0)
    B = pulp.LpVariable.dicts("backlog", T, lowBound=0)

    # Objective: production + overtime + holding + backlog penalty
    m += pulp.lpSum(COST_REGULAR * P[t] + COST_OVERTIME * O[t]
                    + COST_HOLDING * I[t] + backlog_cost * B[t] for t in T)

    # Flow balance: what we had + what we make = what we ship + what we carry
    for t in T:
        prev_inv = OPENING_INVENTORY if t == 0 else I[t - 1]
        prev_backlog = 0 if t == 0 else B[t - 1]
        m += prev_inv + P[t] + O[t] - prev_backlog == DEMAND[t] + I[t] - B[t]

    m += I[T[-1]] >= CLOSING_INVENTORY_MIN
    if clear_backlog_by_dec:
        m += B[T[-1]] == 0

    m.solve(pulp.PULP_CBC_CMD(msg=False))
    return {
        "status": pulp.LpStatus[m.status],
        "cost": pulp.value(m.objective),
        "regular": [P[t].value() for t in T],
        "overtime": [O[t].value() for t in T],
        "inventory": [I[t].value() for t in T],
        "backlog": [B[t].value() for t in T],
    }


def report(name: str, r: dict) -> None:
    print(f"\n=== Scenario {name}: {r['status']}, total cost {r['cost']:,.0f}")
    print(f"{'Month':>5} {'Demand':>8} {'Regular':>9} {'Overtime':>9} {'Inventory':>10} {'Backlog':>9}")
    for i, mth in enumerate(MONTHS):
        print(f"{mth:>5} {DEMAND[i]:>8,} {r['regular'][i]:>9,.0f} {r['overtime'][i]:>9,.0f}"
              f" {r['inventory'][i]:>10,.0f} {r['backlog'][i]:>9,.0f}")


def plot(results: dict) -> None:
    OUT.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, (name, r) in zip(axes, results.items()):
        produced = [a + b for a, b in zip(r["regular"], r["overtime"])]
        ax.plot(MONTHS, DEMAND, marker="o", label="Forecast demand")
        ax.plot(MONTHS, produced, marker="s", label="Production (regular + overtime)")
        ax.plot(MONTHS, r["backlog"], marker="^", label="Backlog")
        ax.set_title(f"Scenario {name.replace('_', ' ')}")
        ax.set_xlabel("Month")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Units")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "scenarios.png", dpi=150)
    print(f"\nChart saved to {OUT / 'scenarios.png'}")


if __name__ == "__main__":
    results = {name: solve(**cfg) for name, cfg in SCENARIOS.items()}
    for name, r in results.items():
        report(name, r)
    plot(results)
