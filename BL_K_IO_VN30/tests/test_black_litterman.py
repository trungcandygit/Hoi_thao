"""
Unit tests cho black_litterman.py — dùng ví dụ nhỏ có nghiệm biết trước.

Tham chiếu: He & Litterman (1999) example (N=2).
"""

import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.black_litterman import (
    bl_posterior,
    compute_equilibrium,
    compute_omega,
    compute_sigma,
    standard_bl_posterior,
)


def make_2asset_example():
    """
    2 tài sản, covariance đơn giản, views rõ ràng.
    """
    sigma = np.array([[0.04, 0.02],
                      [0.02, 0.09]])
    w_mkt = np.array([0.6, 0.4])
    delta = 2.5
    tau   = 1 / 36
    P     = np.array([[1.0, -1.0]])   # view: asset1 outperforms asset2
    q     = np.array([0.02])          # by 2% / month
    return sigma, w_mkt, delta, tau, P, q


def test_equilibrium_shape():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    Pi = compute_equilibrium(sigma, w_mkt, delta)
    assert Pi.shape == (2,), "Π phải có shape (N,)"


def test_equilibrium_values():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    Pi = compute_equilibrium(sigma, w_mkt, delta)
    # Π = δΣw = 2.5 * [[0.04,0.02],[0.02,0.09]] @ [0.6,0.4]
    # = 2.5 * [0.04*0.6+0.02*0.4, 0.02*0.6+0.09*0.4]
    # = 2.5 * [0.032, 0.048] = [0.08, 0.12]
    expected = np.array([0.08, 0.12])
    np.testing.assert_allclose(Pi, expected, rtol=1e-6)


def test_omega_diag_positive():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    Omega = compute_omega(sigma, P, tau, omega_type="diag")
    assert Omega.shape == (1, 1)
    assert Omega[0, 0] > 0, "Omega diagonal phải dương"


def test_omega_full_symmetric():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    P2 = np.array([[1.0, 0.0], [0.0, -1.0]])
    Omega = compute_omega(sigma, P2, tau, omega_type="full")
    np.testing.assert_allclose(Omega, Omega.T, atol=1e-12)


def test_bl_posterior_shape():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    mu, M = bl_posterior(sigma, w_mkt, P, q, tau, delta)
    assert mu.shape == (2,)
    assert M.shape  == (2, 2)


def test_bl_posterior_view_effect():
    """
    Khi có view 'asset1 outperforms asset2 by 2%',
    posterior μ1 - μ2 phải lớn hơn so với equilibrium Π1 - Π2.
    """
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    Pi    = compute_equilibrium(sigma, w_mkt, delta)
    mu, _ = bl_posterior(sigma, w_mkt, P, q, tau, delta)
    # View kéo μ1 - μ2 về phía q[0] = 0.02 (dương)
    assert mu[0] - mu[1] > Pi[0] - Pi[1], (
        "Posterior spread phải lớn hơn equilibrium spread khi view dương"
    )


def test_standard_bl_vs_inverse_bl_no_views():
    """
    Khi view không có (P=zeros, q=0), cả hai công thức nên về gần Π.
    """
    sigma, w_mkt, delta, tau, _, _ = make_2asset_example()
    P = np.zeros((1, 2))
    q = np.zeros(1)
    # Standard BL
    mu_std, _ = standard_bl_posterior(sigma, w_mkt, P, q, tau, delta)
    Pi = compute_equilibrium(sigma, w_mkt, delta)
    # Với P=0, view không có thông tin, posterior ≈ Π
    np.testing.assert_allclose(mu_std, Pi, rtol=0.05)


def test_bl_posterior_positive_definite_M():
    sigma, w_mkt, delta, tau, P, q = make_2asset_example()
    _, M = bl_posterior(sigma, w_mkt, P, q, tau, delta)
    eigenvalues = np.linalg.eigvalsh(M)
    assert np.all(eigenvalues > 0), "Posterior covariance phải positive definite"
