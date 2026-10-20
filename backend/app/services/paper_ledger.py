"""Flat-stake paper ledger against de-vigged 1X2 prices.

The fair probabilities are the proportional normalisation of 1/odds.
Settlement still uses the raw decimal price, so the bookmaker's margin
stays in the payout. This is a historical backtest, not a staking plan.
"""
from __future__ import annotations

OUTCOMES = ("H", "D", "A")
MIN_DECIMAL_ODDS = 1.50
MIN_EDGE = 0.03
STAKE = 1.0


def overround(odds) -> float:
    """sum(1/price) - 1. Zero means the three prices already add up to a fair book."""
    total = 0.0
    for price in odds:
        price = float(price)
        if price <= 0:
            return 0.0
        total += 1.0 / price
    return total - 1.0


def decide(model_probs, fair_probs, odds) -> dict:
    """Pick at most one side.

    A side qualifies only when the model probability beats the de-vigged
    price by MIN_EDGE and the decimal odds are not a short favourite.
    """
    best = None
    saw_short = False
    for side, model_p, fair_p, price in zip(OUTCOMES, model_probs, fair_probs, odds):
        edge = float(model_p) - float(fair_p)
        price = float(price)
        if edge < MIN_EDGE:
            continue
        if price < MIN_DECIMAL_ODDS:
            saw_short = True
            continue
        if best is None or edge > best["edge"]:
            best = {"side": side, "odds": price, "edge": edge, "stake": STAKE}
    if best is not None:
        best["action"] = "bet"
        return best
    return {
        "action": "short_favorite" if saw_short else "thin_edge",
        "side": None,
        "odds": None,
        "edge": None,
        "stake": 0.0,
    }


def settle(side: str, result: str, odds: float, stake: float = STAKE) -> dict:
    won = side == result
    profit = (float(odds) - 1.0) * stake if won else -stake
    return {"won": won, "profit": profit, "staked": stake}


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    hits = sum(1 for row in rows if row["won"])
    staked = float(sum(row["staked"] for row in rows))
    profit = float(sum(row["profit"] for row in rows))
    return {
        "n_bets": n,
        "hits": hits,
        "hit_rate": (hits / n) if n else 0.0,
        "staked": staked,
        "profit": profit,
        "yield": (profit / staked) if staked else 0.0,
    }
