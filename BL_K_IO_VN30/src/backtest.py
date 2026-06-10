"""
Rolling-window OOS backtest (chuẩn DeMiguel et al., 2009).

Cửa sổ ước lượng: 36 tháng (tham số)
Test: 1 tháng kế tiếp
Dynamic basket: chỉ dùng mã có đủ dữ liệu trong cửa sổ
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from .black_litterman import bl_posterior, compute_sigma, standard_bl_posterior
from .clustering import build_view_matrix, fit_kmeans, select_k
from .features import build_features, compute_returns
from .optimizer import (
    apply_transaction_cost,
    equal_weights,
    market_cap_weights,
    optimize_weights,
)

logger = logging.getLogger(__name__)

STRATEGIES = ["BL_K_IO", "BL", "TAN", "MKT", "EW"]


def _get_rf(rf_series: pd.Series, date: pd.Timestamp) -> float:
    """Lấy risk-free rate hàng tháng từ lãi suất năm."""
    rate = rf_series.get(date.year, rf_series.iloc[-1])
    return float(rate) / 12


def run_backtest(
    prices: pd.DataFrame,
    market_cap: pd.DataFrame,
    rf_series: pd.Series,
    estimation_window: int = 36,
    k_range: Tuple[int, int] = (2, 6),
    max_weight: float = 0.30,
    min_weight: float = 0.00,
    delta: float = 2.5,
    omega_type: str = "diag",
    tc_bps: float = 15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Chạy rolling OOS backtest.

    Returns
    -------
    oos_returns : DataFrame (T_oos × n_strategies)  — lợi suất tháng
    weights_log : DataFrame — log trọng số tại mỗi bước
    """
    returns = compute_returns(prices)
    dates   = returns.index
    n_steps = len(dates) - estimation_window

    if n_steps <= 0:
        raise ValueError(
            f"Không đủ dữ liệu: cần ít nhất {estimation_window + 1} tháng, "
            f"có {len(dates)} tháng."
        )

    logger.info("Số bước OOS: %d", n_steps)

    oos_ret: Dict[str, List[float]] = {s: [] for s in STRATEGIES}
    oos_ret_gross: Dict[str, List[float]] = {s: [] for s in STRATEGIES}
    oos_dates: List[pd.Timestamp] = []

    prev_weights: Dict[str, Optional[np.ndarray]] = {s: None for s in STRATEGIES}
    weights_records = []

    tau_val = 1.0 / estimation_window

    for t in tqdm(range(estimation_window, len(dates)), desc="Backtest"):
        test_date = dates[t]
        win_returns = returns.iloc[t - estimation_window : t]

        # Dynamic basket: mã có đủ dữ liệu trong cửa sổ (≥ 90% tháng)
        valid_cols = win_returns.columns[
            win_returns.notna().sum() >= estimation_window * 0.9
        ]
        if len(valid_cols) < 3:
            logger.warning("%s: < 3 mã hợp lệ, bỏ qua bước này.", test_date)
            continue

        r_win  = win_returns[valid_cols].fillna(0).values   # T×N
        n      = len(valid_cols)

        # Sigma
        sigma = compute_sigma(r_win)
        sigma = _regularize(sigma)

        # Market-cap weights
        if test_date in market_cap.index:
            mcap_row = market_cap.loc[test_date, valid_cols].values.astype(float)
        else:
            mcap_row = np.ones(n)
        w_mkt = market_cap_weights(mcap_row)

        # Risk-free (tháng)
        rf = _get_rf(rf_series, test_date)

        # === Chiến lược EW & MKT ===
        w_ew  = equal_weights(n)
        w_market = w_mkt.copy()

        # === TAN (Markowitz tangency) ===
        mu_sample = r_win.mean(axis=0) * 12   # annualized
        sigma_ann = sigma * 12
        w_tan = _safe_optimize(mu_sample, sigma_ann, rf * 12, max_weight, min_weight, seed)

        # === K-means features ===
        feat_df = build_features(
            returns[valid_cols], t, estimation_window,
            market_weights=pd.Series(w_mkt, index=valid_cols),
        )

        # Subset tickers có đặc trưng
        feat_tickers = feat_df.index.tolist()
        feat_idx     = [list(valid_cols).index(tk) for tk in feat_tickers if tk in valid_cols]
        feat_z       = feat_df[["mom_z", "vol_z"]].values

        k_best, _ = select_k(feat_z, k_range, seed)
        km        = fit_kmeans(feat_z, k_best, seed)

        # === BL views ===
        P_feat, q_feat = build_view_matrix(feat_df, km.labels_)

        # Map về full N
        P = np.zeros((2, n))
        for view_row in range(2):
            for fi, gi in enumerate(feat_idx):
                P[view_row, gi] = P_feat[view_row, fi]

        # Chuẩn hóa q sang đơn vị monthly log-return (mean của cụm)
        mu_pi = compute_sigma(r_win) @ w_mkt * delta   # Π theo tháng
        q_scaled = q_feat * float(np.abs(mu_pi).mean())  # scale

        # === BL_K_IO (Inverse BL) ===
        try:
            mu_kio, _ = bl_posterior(sigma, w_mkt, P, q_scaled, tau_val, delta, omega_type)
            mu_kio_ann = mu_kio * 12
            w_kio = _safe_optimize(mu_kio_ann, sigma_ann, rf * 12, max_weight, min_weight, seed)
        except Exception as exc:
            logger.warning("%s BL_K_IO failed: %s — fallback EW", test_date, exc)
            w_kio = w_ew.copy()

        # === BL gốc ===
        try:
            mu_bl, _ = standard_bl_posterior(sigma, w_mkt, P, q_scaled, tau_val, delta, omega_type)
            mu_bl_ann = mu_bl * 12
            w_bl = _safe_optimize(mu_bl_ann, sigma_ann, rf * 12, max_weight, min_weight, seed)
        except Exception as exc:
            logger.warning("%s BL failed: %s — fallback EW", test_date, exc)
            w_bl = w_ew.copy()

        # === Tính lợi suất tháng test ===
        r_test = returns.loc[test_date, valid_cols].fillna(0).values

        strat_weights = {
            "BL_K_IO": w_kio,
            "BL":      w_bl,
            "TAN":     w_tan,
            "MKT":     w_market,
            "EW":      w_ew,
        }

        oos_dates.append(test_date)
        for s, w in strat_weights.items():
            gross = float(w @ r_test)
            net   = apply_transaction_cost(gross, w, prev_weights[s], tc_bps)
            oos_ret[s].append(net)
            oos_ret_gross[s].append(gross)
            prev_weights[s] = w.copy()

        weights_records.append({
            "date": test_date,
            "strategy": "BL_K_IO",
            "k": k_best,
            "n_assets": n,
            **{f"w_{tk}": strat_weights["BL_K_IO"][i]
               for i, tk in enumerate(valid_cols)},
        })

    oos_df = pd.DataFrame(oos_ret, index=oos_dates)
    oos_df.index.name = "date"
    weights_df = pd.DataFrame(weights_records).set_index("date")

    logger.info("Backtest hoàn thành: %d bước OOS.", len(oos_df))
    return oos_df, weights_df


def _regularize(sigma: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Thêm ridge nhỏ để đảm bảo positive definite."""
    return sigma + eps * np.eye(sigma.shape[0])


def _safe_optimize(mu, sigma, rf, max_w, min_w, seed) -> np.ndarray:
    try:
        return optimize_weights(mu, sigma, rf, max_w, min_w, seed=seed)
    except Exception as exc:
        logger.warning("Optimize failed: %s — fallback EW", exc)
        return equal_weights(len(mu))
