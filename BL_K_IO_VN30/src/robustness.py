"""
Phân tích robustness:
  1. Quét ESTIMATION_WINDOW × MAX_WEIGHT × k
  2. Monte Carlo nhiễu loạn vector q (±5%, ±10%)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from .backtest import run_backtest
from .metrics import compute_all_metrics

logger = logging.getLogger(__name__)


def param_sweep(
    prices: pd.DataFrame,
    market_cap: pd.DataFrame,
    rf_series: pd.Series,
    estimation_windows: List[int],
    max_weights: List[float],
    k_values: List[int],
    base_cfg: dict,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Quét tham số, trả bảng Sharpe (BL_K_IO) cho mỗi tổ hợp.
    """
    records = []
    for ew in estimation_windows:
        for mw in max_weights:
            for k in k_values:
                logger.info("Sweep: window=%d, max_w=%.2f, k=%d", ew, mw, k)
                try:
                    oos, _ = run_backtest(
                        prices, market_cap, rf_series,
                        estimation_window=ew,
                        k_range=(k, k),   # fix k
                        max_weight=mw,
                        min_weight=base_cfg["model"]["min_weight"],
                        delta=base_cfg["model"]["delta"],
                        omega_type=base_cfg["model"]["omega_type"],
                        tc_bps=base_cfg["model"]["tc_bps"],
                        seed=seed,
                    )
                    metrics = compute_all_metrics(oos, rf_series)
                    row = metrics[
                        (metrics["period"] == "full") &
                        (metrics["strategy"] == "BL_K_IO")
                    ].iloc[0]
                    records.append({
                        "estimation_window": ew,
                        "max_weight": mw,
                        "k": k,
                        "sharpe": row["sharpe"],
                        "ann_return": row["ann_return"],
                        "ann_std": row["ann_std"],
                        "max_drawdown": row["max_drawdown"],
                    })
                except Exception as exc:
                    logger.warning("Sweep failed (%d, %.2f, %d): %s", ew, mw, k, exc)

    return pd.DataFrame(records)


def monte_carlo_q(
    prices: pd.DataFrame,
    market_cap: pd.DataFrame,
    rf_series: pd.Series,
    perturbations: List[float],
    n_scenarios: int,
    base_cfg: dict,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Monte Carlo: nhiễu loạn vector q theo ±perturb%, chạy n_scenarios lần.
    Trả phân phối Sharpe của BL_K_IO.
    """
    from .backtest import STRATEGIES, _get_rf, _regularize, _safe_optimize
    from .black_litterman import bl_posterior
    from .clustering import build_view_matrix, fit_kmeans, select_k
    from .features import build_features, compute_returns
    from .optimizer import apply_transaction_cost, equal_weights, market_cap_weights

    estimation_window = base_cfg["model"]["estimation_window"]
    k_range = tuple(base_cfg["model"]["n_clusters_range"])
    max_weight = base_cfg["model"]["max_weight"]
    min_weight = base_cfg["model"]["min_weight"]
    delta = base_cfg["model"]["delta"]
    omega_type = base_cfg["model"]["omega_type"]
    tc_bps = base_cfg["model"]["tc_bps"]
    tau = 1.0 / estimation_window

    returns_df = compute_returns(prices)
    dates = returns_df.index

    records = []
    for perturb in perturbations:
        rng = np.random.default_rng(seed)
        scenario_sharpes = []
        logger.info("MC perturbation ±%.0f%%: %d scenarios", perturb * 100, n_scenarios)

        for scen in tqdm(range(n_scenarios), desc=f"MC ±{perturb*100:.0f}%"):
            scen_rets = []
            for t in range(estimation_window, len(dates)):
                test_date = dates[t]
                win_returns = returns_df.iloc[t - estimation_window : t]
                valid_cols = win_returns.columns[
                    win_returns.notna().sum() >= estimation_window * 0.9
                ]
                if len(valid_cols) < 3:
                    continue

                r_win = win_returns[valid_cols].fillna(0).values
                n = len(valid_cols)
                sigma = _regularize(np.cov(r_win.T, ddof=1))
                sigma_ann = sigma * 12

                if test_date in market_cap.index:
                    mcap_row = market_cap.loc[test_date, valid_cols].values.astype(float)
                else:
                    mcap_row = np.ones(n)
                w_mkt = market_cap_weights(mcap_row)
                rf = _get_rf(rf_series, test_date)

                feat_df = build_features(
                    returns_df[valid_cols], t, estimation_window,
                    market_weights=pd.Series(w_mkt, index=valid_cols),
                )
                feat_tickers = feat_df.index.tolist()
                feat_idx = [list(valid_cols).index(tk) for tk in feat_tickers if tk in valid_cols]
                feat_z = feat_df[["mom_z", "vol_z"]].values

                k_best, _ = select_k(feat_z, k_range, seed + scen)
                km = fit_kmeans(feat_z, k_best, seed + scen)
                P_feat, q_feat = build_view_matrix(feat_df, km.labels_)

                P = np.zeros((2, n))
                for row_i in range(2):
                    for fi, gi in enumerate(feat_idx):
                        P[row_i, gi] = P_feat[row_i, fi]

                mu_pi = sigma @ w_mkt * delta
                q_base = q_feat * float(np.abs(mu_pi).mean())
                # Nhiễu loạn q
                noise = rng.uniform(1 - perturb, 1 + perturb, size=q_base.shape)
                q_perturbed = q_base * noise

                try:
                    mu_kio, _ = bl_posterior(sigma, w_mkt, P, q_perturbed, tau, delta, omega_type)
                    w_kio = _safe_optimize(mu_kio * 12, sigma_ann, rf * 12, max_weight, min_weight, seed)
                except Exception:
                    w_kio = equal_weights(n)

                r_test = returns_df.loc[test_date, valid_cols].fillna(0).values
                scen_rets.append(float(w_kio @ r_test))

            if scen_rets:
                r_arr = np.array(scen_rets)
                sr = r_arr.mean() / r_arr.std(ddof=1) * np.sqrt(12) if r_arr.std(ddof=1) > 0 else 0
                scenario_sharpes.append(sr)

        if scenario_sharpes:
            arr = np.array(scenario_sharpes)
            records.append({
                "perturbation": perturb,
                "mean_sharpe":  arr.mean(),
                "std_sharpe":   arr.std(ddof=1),
                "p5_sharpe":    np.percentile(arr, 5),
                "p95_sharpe":   np.percentile(arr, 95),
                "n_scenarios":  len(arr),
            })

    return pd.DataFrame(records)
