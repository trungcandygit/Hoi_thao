"""
Unit tests cho optimizer.py.
"""

import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.optimizer import (
    apply_transaction_cost,
    equal_weights,
    market_cap_weights,
    optimize_weights,
)


def make_simple_problem(n: int = 3):
    """
    Tạo bài toán tối ưu đơn giản với nghiệm biết trước.
    Khi μ = [0.1, 0.05, 0.03] và Σ = diag([0.04, 0.04, 0.04]),
    Sharpe max ở weight toàn bộ vào tài sản 1 (nếu không có trần).
    """
    mu    = np.array([0.10, 0.05, 0.03])
    sigma = np.diag([0.04, 0.04, 0.04])
    rf    = 0.02
    return mu, sigma, rf


def test_optimize_weights_sums_to_one():
    mu, sigma, rf = make_simple_problem()
    w = optimize_weights(mu, sigma, rf, max_weight=0.30)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-6)


def test_optimize_weights_bounds_respected():
    # Dùng n=4 để max_w=0.30 feasible (1/4=0.25 < 0.30)
    mu    = np.array([0.10, 0.07, 0.05, 0.03])
    sigma = np.diag([0.04, 0.04, 0.04, 0.04])
    rf    = 0.02
    max_w = 0.30
    w = optimize_weights(mu, sigma, rf, max_weight=max_w, min_weight=0.0)
    assert np.all(w >= -1e-8), "Trọng số phải >= 0"
    assert np.all(w <= max_w + 1e-6), f"Trọng số phải <= {max_w}"
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-5)


def test_optimize_weights_higher_return_gets_more():
    """
    Tài sản có return cao nhất nên có trọng số cao nhất (ít nhất bằng tài sản 3).
    """
    mu, sigma, rf = make_simple_problem()
    w = optimize_weights(mu, sigma, rf, max_weight=0.50)
    assert w[0] >= w[2], "Tài sản 1 (return cao) nên có trọng số >= tài sản 3"


def test_market_cap_weights_sum():
    mcap = np.array([100., 200., 300.])
    w = market_cap_weights(mcap)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-10)
    np.testing.assert_allclose(w, [1/6, 2/6, 3/6], atol=1e-10)


def test_market_cap_weights_all_nan():
    mcap = np.array([np.nan, np.nan])
    w = market_cap_weights(mcap)
    np.testing.assert_allclose(w, [0.5, 0.5], atol=1e-10)


def test_equal_weights():
    for n in [2, 5, 10]:
        w = equal_weights(n)
        assert len(w) == n
        np.testing.assert_allclose(w.sum(), 1.0, atol=1e-10)
        np.testing.assert_allclose(w, np.ones(n) / n)


def test_transaction_cost_reduces_return():
    ret = 0.05
    w_new  = np.array([0.4, 0.4, 0.2])
    w_prev = np.array([0.2, 0.4, 0.4])
    net = apply_transaction_cost(ret, w_new, w_prev, tc_bps=15)
    assert net < ret, "Net return phải nhỏ hơn gross return sau TC"


def test_transaction_cost_zero_turnover():
    """Nếu không thay đổi trọng số, TC = 0."""
    w = np.array([0.3, 0.4, 0.3])
    net = apply_transaction_cost(0.05, w, w.copy(), tc_bps=15)
    np.testing.assert_allclose(net, 0.05, atol=1e-10)


def test_transaction_cost_first_period():
    """Kỳ đầu tiên (w_prev=None) không trừ TC."""
    net = apply_transaction_cost(0.05, np.array([0.5, 0.5]), None, tc_bps=15)
    np.testing.assert_allclose(net, 0.05)


def test_optimize_4asset_known_solution():
    """
    4 tài sản với Σ = I*0.01, μ = [0.12, 0.10, 0.08, 0.06], rf=0.
    Tangency = max Sharpe = đặt toàn bộ vào tài sản 1 (nếu max_weight >= 1).
    Với max_weight=0.5, 2 tài sản đầu nên chiếm phần lớn.
    """
    mu    = np.array([0.12, 0.10, 0.08, 0.06])
    sigma = np.eye(4) * 0.01
    rf    = 0.0
    w = optimize_weights(mu, sigma, rf, max_weight=0.50)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-5)
    assert w[0] + w[1] > w[2] + w[3], "2 tài sản đầu nên được ưu tiên hơn"
