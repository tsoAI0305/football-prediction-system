from app.services.paper_ledger import MIN_DECIMAL_ODDS, MIN_EDGE, decide, overround, settle, summarize


def test_overround_is_zero_for_a_fair_book():
    assert abs(overround((2.0, 4.0, 4.0))) < 1e-9


def test_short_favourite_with_a_large_edge_is_skipped():
    decision = decide(
        model_probs=(0.80, 0.12, 0.08),
        fair_probs=(0.70, 0.18, 0.12),
        odds=(1.20, 6.0, 9.0),
    )
    assert decision["action"] == "short_favorite"
    assert decision["odds"] is None
    assert 1.20 < MIN_DECIMAL_ODDS


def test_thin_edge_is_skipped():
    decision = decide(
        model_probs=(0.46, 0.28, 0.26),
        fair_probs=(0.45, 0.30, 0.25),
        odds=(2.2, 3.4, 4.0),
    )
    assert decision["action"] == "thin_edge"
    assert decision["edge"] is None
    assert 0.01 < MIN_EDGE


def test_qualifying_side_is_the_larger_edge_not_the_short_price():
    decision = decide(
        model_probs=(0.70, 0.22, 0.08),
        fair_probs=(0.60, 0.15, 0.25),
        odds=(1.30, 3.50, 8.0),
    )
    assert decision["action"] == "bet"
    assert decision["side"] == "D"
    assert decision["odds"] == 3.50


def test_settle_flat_stake_and_yield():
    win = settle("H", "H", 2.0)
    loss = settle("H", "A", 2.0)
    assert win["profit"] == 1.0
    assert loss["profit"] == -1.0
    summary = summarize([win, loss])
    assert summary["n_bets"] == 2
    assert summary["hits"] == 1
    assert summary["hit_rate"] == 0.5
    assert summary["yield"] == 0.0


def test_empty_ledger_has_no_yield():
    summary = summarize([])
    assert summary["n_bets"] == 0
    assert summary["yield"] == 0.0
