"""
Tính toán các chỉ số hiệu suất và kiểm định thống kê.

Chỉ số:
  - Annualized Return, Annualized Std, Sharpe, Sortino, Max Drawdown
  - Sharpe trước và sau phí giao dịch

Kiểm định:
  - Ledoit-Wolf (2008) / Jobson-Korkie bootstrap cho chênh lệch Sharpe
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def annualized_return(r: pd.Series, freq: int = 12) -> float:
    return float(r.mean() * freq)


def annualized_std(r: pd.Series, freq: int = 12) -> float:
    return float(r.std(ddof=1) * np.sqrt(freq))


def sharpe(r: pd.Series, rf_monthly: float = 0.0, freq: int = 12) -> float:
    excess = r - rf_monthly
    std = excess.std(ddof=1)
    if std < 1e-12:
        return 0.0
    return float(excess.mean() / std * np.sqrt(freq))


def sortino(r: pd.Series, rf_monthly: float = 0.0, freq: int = 12) -> float:
    excess = r - rf_monthly
    downside = excess[excess < 0]
    ds_std = downside.std(ddof=1) if len(downside) > 1 else 1e-12
    if ds_std < 1e-12:
        return 0.0
    return float(excess.mean() / ds_std * np.sqrt(freq))


def max_drawdown(r: pd.Series) -> float:
    cum = (1 + r).cumprod()
    roll_max = cum.cummax()
    dd = (cum - roll_max) / roll_max
    return float(dd.min())


def compute_all_metrics(
    returns: pd.DataFrame,
    rf_series: pd.Series,
    sub_periods: Optional[Dict[str, Dict]] = None,
    freq: int = 12,
) -> pd.DataFrame:
    """
    Tính bảng chỉ số cho tất cả chiến lược.

    Parameters
    ----------
    returns    : DataFrame (dates × strategies) — net returns
    rf_series  : Series year → annual rate
    sub_periods: {'bull': {'start':..,'end':..}, 'disrupted': ...}
    """
    periods = {"full": (returns.index[0], returns.index[-1])}
    if sub_periods:
        for name, rng in sub_periods.items():
            periods[name] = (pd.Timestamp(rng["start"]), pd.Timestamp(rng["end"]))

    records = []
    for period_name, (p_start, p_end) in periods.items():
        sub = returns.loc[p_start:p_end]
        for col in sub.columns:
            r = sub[col].dropna()
            if r.empty:
                continue
            # Bình quân rf tháng trong khoảng này
            rf_avg = _avg_rf(rf_series, p_start, p_end) / freq
            records.append({
                "period":      period_name,
                "strategy":    col,
                "ann_return":  annualized_return(r, freq),
                "ann_std":     annualized_std(r, freq),
                "sharpe":      sharpe(r, rf_avg, freq),
                "sortino":     sortino(r, rf_avg, freq),
                "max_drawdown": max_drawdown(r),
                "n_months":    len(r),
            })

    df = pd.DataFrame(records)
    return df


def _avg_rf(rf_series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    years = list(range(start.year, end.year + 1))
    rates = [rf_series.get(y, float(rf_series.iloc[-1])) for y in years]
    return float(np.mean(rates))


# ---------------------------------------------------------------------------
# Sharpe difference test
# ---------------------------------------------------------------------------

def bootstrap_sharpe_diff(
    r1: pd.Series,
    r2: pd.Series,
    n_boot: int = 5000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """
    Bootstrap test: H0: Sharpe(r1) = Sharpe(r2).

    Returns
    -------
    diff_obs : observed Sharpe(r1) - Sharpe(r2)
    p_value  : two-sided p-value
    ci_95    : (lower, upper) 95% confidence interval of the difference
    """
    rng = np.random.default_rng(seed)
    n   = min(len(r1), len(r2))
    r1_, r2_ = r1.values[-n:], r2.values[-n:]

    def _sr(x: np.ndarray) -> float:
        s = x.std(ddof=1)
        return x.mean() / s * np.sqrt(12) if s > 0 else 0.0

    diff_obs = _sr(r1_) - _sr(r2_)
    diffs_boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs_boot.append(_sr(r1_[idx]) - _sr(r2_[idx]))

    diffs_boot = np.array(diffs_boot)
    # Two-sided p-value: fraction of bootstrap samples more extreme than diff_obs under H0
    centered = diffs_boot - diffs_boot.mean()
    p_value  = float(np.mean(np.abs(centered) >= np.abs(diff_obs)))
    ci_low, ci_high = float(np.percentile(diffs_boot, 2.5)), float(np.percentile(diffs_boot, 97.5))

    return diff_obs, p_value, (ci_low, ci_high)


def pairwise_sharpe_tests(
    returns: pd.DataFrame,
    baseline: str = "BL_K_IO",
    n_boot: int = 5000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Kiểm định Bootstrap Sharpe cho từng cặp (baseline vs. others).
    """
    records = []
    r1 = returns[baseline].dropna()
    for col in returns.columns:
        if col == baseline:
            continue
        r2 = returns[col].dropna()
        diff, pval, (ci_l, ci_h) = bootstrap_sharpe_diff(r1, r2, n_boot, seed)
        records.append({
            "strategy_A": baseline,
            "strategy_B": col,
            "sharpe_diff": diff,
            "p_value": pval,
            "ci_95_low": ci_l,
            "ci_95_high": ci_h,
            "significant_5pct": pval < 0.05,
        })
    return pd.DataFrame(records)
