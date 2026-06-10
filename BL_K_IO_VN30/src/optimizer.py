"""
Tối ưu trọng số danh mục bằng SLSQP, cực đại Sharpe ratio.

Chiến lược
----------
BL_K_IO  : μ = bl_posterior (Inverse BL), Σ từ dữ liệu
BL       : μ = standard_bl_posterior,     Σ từ dữ liệu
TAN      : μ = sample mean,               Σ từ dữ liệu (Markowitz tangency)
MKT      : w = market-cap weights (không tối ưu)
EW       : w = 1/N                        (không tối ưu)
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


def _sharpe_neg(w: np.ndarray, mu: np.ndarray, sigma: np.ndarray, rf: float) -> float:
    port_ret = w @ mu
    port_vol = np.sqrt(w @ sigma @ w)
    if port_vol < 1e-12:
        return 0.0
    return -(port_ret - rf) / port_vol


def optimize_weights(
    mu: np.ndarray,
    sigma: np.ndarray,
    rf: float,
    max_weight: float = 0.30,
    min_weight: float = 0.00,
    n_restarts: int = 5,
    seed: int = 42,
) -> np.ndarray:
    """
    SLSQP: max Sharpe(w) s.t. Σw=1, min_weight ≤ w ≤ max_weight.

    Trả trọng số (N,).
    """
    n = len(mu)
    # Đảm bảo bài toán feasible: max_weight >= 1/n
    effective_max = max(max_weight, 1.0 / n)
    if effective_max > max_weight:
        logger.debug("max_weight %.2f nâng lên %.4f để đảm bảo feasibility với n=%d",
                     max_weight, effective_max, n)
    max_weight = effective_max
    bounds = [(min_weight, max_weight)] * n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]

    rng = np.random.default_rng(seed)
    best_val, best_w = np.inf, np.ones(n) / n

    for _ in range(n_restarts):
        w0 = rng.dirichlet(np.ones(n))
        result = minimize(
            _sharpe_neg,
            w0,
            args=(mu, sigma, rf),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )
        if result.fun < best_val:
            best_val = result.fun
            best_w   = result.x

    # Project lên simplex có bounds [min_weight, max_weight] bằng iterative clamping
    best_w = _project_simplex(best_w, min_weight, max_weight)
    return best_w


def market_cap_weights(mcap: np.ndarray) -> np.ndarray:
    """w_i = mcap_i / Σ mcap_j. Nếu tất cả NaN → equal weight."""
    if np.all(np.isnan(mcap)):
        n = len(mcap)
        return np.ones(n) / n
    w = np.where(np.isnan(mcap), 0.0, mcap)
    total = w.sum()
    if total <= 0:
        return np.ones(len(mcap)) / len(mcap)
    return w / total


def equal_weights(n: int) -> np.ndarray:
    return np.ones(n) / n


def _project_simplex(w: np.ndarray, lo: float, hi: float, max_iter: int = 100) -> np.ndarray:
    """
    Project w lên simplex {Σwᵢ=1, lo≤wᵢ≤hi} bằng iterative clamping.
    Bảo đảm Σwᵢ=1 sau mỗi vòng lặp.
    """
    n = len(w)
    w = w.copy()
    for _ in range(max_iter):
        w_prev = w.copy()
        # Clamp về [lo, hi]
        w = np.clip(w, lo, hi)
        # Renormalize: chia cho tổng (cần sum > 0)
        s = w.sum()
        if s > 0:
            w = w / s
        # Kiểm tra hội tụ
        if np.max(np.abs(w - w_prev)) < 1e-10:
            break
    # Lần cuối: đảm bảo bounds sau renorm bằng cách cắt và phân bổ lại dư
    w = np.clip(w, lo, hi)
    excess = w.sum() - 1.0
    if abs(excess) > 1e-9:
        # Giảm bớt các weight không bị ràng buộc
        free  = (w > lo + 1e-10) if excess > 0 else (w < hi - 1e-10)
        if free.any():
            w[free] -= excess / free.sum()
        w = np.clip(w, lo, hi)
    return w


def apply_transaction_cost(
    ret: float,
    w_new: np.ndarray,
    w_prev: np.ndarray | None,
    tc_bps: float = 15,
) -> float:
    """
    Khấu trừ chi phí giao dịch theo turnover.

    cost = tc_bps / 10000 * turnover
    turnover = 0.5 * Σ|w_new - w_prev|  (one-way)
    """
    if w_prev is None:
        return ret
    turnover = 0.5 * np.abs(w_new - w_prev).sum()
    cost = tc_bps / 10_000 * turnover
    return ret - cost
