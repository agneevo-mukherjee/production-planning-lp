# Production Planning with Linear Programming (PuLP)

A 12-month production and inventory plan for UOB Clothing's swimwear product, built as a linear programme in Python. With the costs given in the coursework brief, the cost-minimising plan **produces nothing and defers all demand**. This repo shows why, and how the recommendations from my report change the plan.

*MSc Data Science for Business, University of Bristol · Supply Chain Analytics · 2026*

![Scenario comparison](outputs/scenarios.png)

## The problem

UOB Clothing, an online fast-fashion company in the UK, needs to decide how many swimwear units to make each month in 2025, using regular production, overtime or stored inventory, at the lowest total cost.

**Demand** comes from my 12-month forecast built in R (Part 1 of the coursework). I compared Holt's linear trend method with **Holt-Winters exponential smoothing (multiplicative seasonality)** on 36 months of sales (Jan 2022 – Dec 2024). Holt-Winters fitted best (MAE 213.9 · RMSE 260.5 · **MAPE 2.90%**) and forecasts a June 2025 peak of about 15,197 units.

**Parameters** (as set in the coursework brief):

| Input | Value |
|---|---|
| Regular production | £8.00 per unit, up to 14,500 units/month |
| Overtime production | £12.00 per unit, up to 1,450 units/month |
| Holding cost | £0.17 per unit per month |
| Backlog (stockout) penalty | £0.50 per unit per month |
| Opening and minimum closing inventory | 500 units |

## The model

For each month *t*, the decision variables are regular production *Pₜ*, overtime *Oₜ*, ending inventory *Iₜ* and backlog *Bₜ* (unmet demand carried forward).

**Minimise** Σ (8·Pₜ + 12·Oₜ + 0.17·Iₜ + b·Bₜ)

**Subject to**
- Flow balance: Iₜ₋₁ − Bₜ₋₁ + Pₜ + Oₜ = Dₜ + Iₜ − Bₜ
- Capacity: Pₜ ≤ 14,500 and Oₜ ≤ 1,450
- Closing inventory: I₁₂ ≥ 500
- Scenario B only: no backlog left at year end (B₁₂ = 0)

## Results

| | **A · Submitted coursework** | **B · Extension (after submission)** |
|---|---|---|
| Backlog penalty (*b*) | £0.50 per unit per month (brief) | £15.00 per unit per month (illustrative) |
| Backlog must be cleared by December | No | Yes |
| Units produced | **0** | 130,411 |
| Backlog in December | **130,411 units** | 0 |
| Total cost | ≈ £413,450 | ≈ £1,043,490 |

**Scenario A** is the result in my submitted report. It looks cheap only because it never produces anything: a £0.50 backlog penalty is far below the £8.00 cost of making a unit, so the solver defers every order, all year. Mathematically optimal, operationally unrealistic.

My report made three recommendations:
1. Re-evaluate the backlog cost so it reflects lost sales and customer dissatisfaction
2. Add service-level constraints so demand is actually fulfilled
3. Produce proactively before peak months

**Scenario B** applies all three. With the backlog penalty set above the overtime cost and backlog cleared by December, the plan meets demand month by month. It also builds about 700 units of stock in **May**, because June's forecast (15,197) exceeds regular capacity (14,500), and making units early and storing them (£8.17) is cheaper than overtime (£12.00).

## What this shows

- An optimisation model is only as good as its costs. When a penalty is mispriced, the "optimal" answer can be the opposite of what the business wants.
- Service-level constraints are a simple guard against plans that look cheap on paper.
- Check the solution, not just the solver status: both scenarios report "Optimal".

## Run it

```bash
pip install -r requirements.txt
python production_planning.py
```

This prints both monthly plans and saves the chart to `outputs/scenarios.png`.

*Note: the code uses the classic PuLP 2.x API, so `requirements.txt` pins `pulp<3`.*

## Files

| File | What it is |
|---|---|
| `production_planning.py` | The model, both scenarios, results table and chart |
| `requirements.txt` | Python dependencies |
| `outputs/scenarios.png` | Demand, production and backlog for each scenario |

*Notes: this is a tidied version of my coursework code, with parameters gathered at the top and the flow-balance constraint written in its standard form (backlog carried in is added to the month's requirement). Scenario A matches my report's result; totals differ by a few pounds because of rounding. The forecasting work in R will be in a separate repo.*
