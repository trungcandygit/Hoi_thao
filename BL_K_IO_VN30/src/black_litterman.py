"""
Inverse Black-Litterman (Bertsimas et al., 2012).

Công thức
---------
Equilibrium:
  Π = δ Σ w_mkt

Uncertainty on views:
  Ω = τ P Σ Pᵀ        (hoặc diag của biểu thức này)
  τ = 1 / estimation_window

Posterior mean:
  μ = [(τΣ)⁻¹ + Pᵀ Ω⁻¹ P]⁻¹ [(τΣ)⁻¹ Π + Pᵀ Ω⁻¹ q]

Posterior covariance (nếu cần):
  M = [(τΣ)⁻¹ + Pᵀ Ω⁻¹ P]⁻¹
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)


def compute_sigma(returns: np.ndarray) -> np.ndarray:
    """Hiệp phương sai mẫu từ ma trận returns (T×N)."""
    return np.cov(returns.T, ddof=1)


def compute_equilibrium(
    sigma: np.ndarray,
    w_mkt: np.ndarray,
    delta: float = 2.5,
) -> np.ndarray:
    """Π = δ Σ w_mkt"""
    return delta * sigma @ w_mkt


def compute_omega(
    sigma: np.ndarray,
    P: np.ndarray,
    tau: float,
    omega_type: Literal["diag", "full"] = "diag",
) -> np.ndarray:
    """
    Ω = τ P Σ Pᵀ  (full) hoặc diag(τ P Σ Pᵀ) (diag).
    """
    PSPt = tau * P @ sigma @ P.T
    if omega_type == "diag":
        return np.diag(np.diag(PSPt))
    return PSPt


def bl_posterior(
    sigma: np.ndarray,
    w_mkt: np.ndarray,
    P: np.ndarray,
    q: np.ndarray,
    tau: float,
    delta: float = 2.5,
    omega_type: Literal["diag", "full"] = "diag",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Tính posterior mean và covariance theo Black-Litterman.

    Returns
    -------
    mu_post : ndarray shape (N,)
    M       : ndarray shape (N, N)  — posterior covariance
    """
    Pi = compute_equilibrium(sigma, w_mkt, delta)
    Omega = compute_omega(sigma, P, tau, omega_type)

    tau_sigma_inv = np.linalg.inv(tau * sigma)
    Omega_inv     = np.linalg.inv(Omega)

    # A = (τΣ)⁻¹ + Pᵀ Ω⁻¹ P
    A = tau_sigma_inv + P.T @ Omega_inv @ P
    # b = (τΣ)⁻¹ Π + Pᵀ Ω⁻¹ q
    b = tau_sigma_inv @ Pi + P.T @ Omega_inv @ q

    M = np.linalg.inv(A)
    mu_post = M @ b

    return mu_post, M


def standard_bl_posterior(
    sigma: np.ndarray,
    w_mkt: np.ndarray,
    P: np.ndarray,
    q: np.ndarray,
    tau: float,
    delta: float = 2.5,
    omega_type: Literal["diag", "full"] = "diag",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Black-Litterman gốc (He & Litterman, 1999) — không có Inverse component.
    Dùng làm benchmark "BL".

    μ_BL = Π + τΣPᵀ(PτΣPᵀ + Ω)⁻¹(q - PΠ)
    """
    Pi    = compute_equilibrium(sigma, w_mkt, delta)
    Omega = compute_omega(sigma, P, tau, omega_type)

    tauS  = tau * sigma
    inner = P @ tauS @ P.T + Omega + np.eye(Omega.shape[0]) * 1e-10
    K     = tauS @ P.T @ np.linalg.inv(inner)
    mu_bl = Pi + K @ (q - P @ Pi)

    Sigma_post = sigma + tauS - K @ P @ tauS
    return mu_bl, Sigma_post
