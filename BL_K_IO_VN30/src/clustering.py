"""
K-means clustering và lựa chọn số cụm k tối ưu.

Tiêu chí lựa chọn k:
  1. Elbow (inertia / WCSS)
  2. Silhouette score
  3. Calinski-Harabasz index
  4. Davies-Bouldin index  (nhỏ hơn = tốt hơn)
  5. Gap statistic

Cách map cụm → view vector (P, q)
-----------------------------------
- Tính mean momentum z-score của mỗi cụm.
- Cụm có mean cao nhất = "winner cluster" → long view.
- Cụm có mean thấp nhất = "loser cluster"  → short view.
- P: ma trận (2 × N) với P[0, i]=1/|winner| nếu i ∈ winner, P[1, i]=-1/|loser| nếu i ∈ loser.
  → Mỗi view là portfolio long hoặc short.
- q: [q_long, q_short] được tính từ mean μ của cụm (xem inverse_bl).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

logger = logging.getLogger(__name__)


def _gap_statistic(
    X: np.ndarray,
    k: int,
    n_refs: int = 10,
    seed: int = 42,
) -> Tuple[float, float]:
    """
    Gap(k) = E*[log W_k] - log W_k  (Tibshirani et al., 2001).
    Trả (gap, sk).
    """
    rng = np.random.default_rng(seed)

    km = KMeans(n_clusters=k, n_init=10, random_state=seed)
    km.fit(X)
    log_wk = np.log(km.inertia_)

    ref_log_wks = []
    mins, maxs = X.min(axis=0), X.max(axis=0)
    for _ in range(n_refs):
        rand_X = rng.uniform(mins, maxs, size=X.shape)
        km_ref = KMeans(n_clusters=k, n_init=10, random_state=seed)
        km_ref.fit(rand_X)
        ref_log_wks.append(np.log(km_ref.inertia_))

    ref_arr = np.array(ref_log_wks)
    gap = ref_arr.mean() - log_wk
    sdk = ref_arr.std(ddof=1)
    sk = sdk * np.sqrt(1 + 1 / n_refs)
    return gap, sk


def select_k(
    feat_z: np.ndarray,
    k_range: Tuple[int, int] = (2, 6),
    seed: int = 42,
) -> Tuple[int, pd.DataFrame]:
    """
    Quét k = k_range[0]..k_range[1], tính 5 tiêu chí.
    Trả k được đề xuất (đa số phiếu) và bảng chỉ số.

    Quy tắc voting:
      - Elbow: k trước khi inertia giảm chậm nhất (knee)
      - Silhouette: argmax
      - Calinski-Harabasz: argmax
      - Davies-Bouldin: argmin
      - Gap: k nhỏ nhất thoả Gap(k) >= Gap(k+1) - s(k+1)
    """
    k_vals = list(range(k_range[0], k_range[1] + 1))
    records = []

    for k in k_vals:
        km = KMeans(n_clusters=k, n_init=20, random_state=seed)
        labels = km.fit_predict(feat_z)

        inertia   = km.inertia_
        sil       = silhouette_score(feat_z, labels)    if k > 1 else np.nan
        ch        = calinski_harabasz_score(feat_z, labels) if k > 1 else np.nan
        db        = davies_bouldin_score(feat_z, labels)    if k > 1 else np.nan
        gap, s_k  = _gap_statistic(feat_z, k, seed=seed)

        records.append(dict(k=k, inertia=inertia, silhouette=sil,
                            calinski=ch, davies_bouldin=db, gap=gap, gap_sk=s_k))

    df = pd.DataFrame(records).set_index("k")

    # --- voting ---
    votes: Dict[int, int] = {k: 0 for k in k_vals}

    # Elbow: second derivative of inertia
    inertias = df["inertia"].values
    if len(inertias) >= 3:
        d2 = np.diff(inertias, 2)
        elbow_k = k_vals[int(np.argmax(d2)) + 1]
        votes[elbow_k] += 1

    votes[int(df["silhouette"].idxmax())] += 1
    votes[int(df["calinski"].idxmax())]   += 1
    votes[int(df["davies_bouldin"].idxmin())] += 1

    # Gap: smallest k s.t. gap(k) >= gap(k+1) - sk+1
    best_gap_k = k_vals[-1]
    for i, k in enumerate(k_vals[:-1]):
        next_k = k_vals[i + 1]
        if df.loc[k, "gap"] >= df.loc[next_k, "gap"] - df.loc[next_k, "gap_sk"]:
            best_gap_k = k
            break
    votes[best_gap_k] += 1

    best_k = max(votes, key=lambda x: (votes[x], -x))  # tie-break: prefer smaller k
    logger.debug("K-selection votes: %s → best k=%d", votes, best_k)
    return best_k, df


def fit_kmeans(
    feat_z: np.ndarray,
    k: int,
    seed: int = 42,
) -> KMeans:
    km = KMeans(n_clusters=k, n_init=20, random_state=seed)
    km.fit(feat_z)
    return km


def build_view_matrix(
    feat: pd.DataFrame,
    labels: np.ndarray,
    mu_posterior: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Xây dựng P (2×N) và q (2,) cho Black-Litterman.

    - feat: DataFrame với index = tickers, cột bao gồm 'mom_z'.
    - labels: cluster label cho mỗi ticker (cùng thứ tự với feat.index).
    - mu_posterior: nếu không None, dùng mean posterior của cụm làm q;
                    nếu None, dùng mean idio_mom của cụm làm q proxy.

    Trả P, q sao cho view = "winner cluster outperforms loser cluster".
    """
    tickers = feat.index.tolist()
    n = len(tickers)
    unique_k = np.unique(labels)

    # mean momentum z-score của mỗi cụm → xếp hạng
    cluster_score = {
        k: feat["mom_z"].values[labels == k].mean()
        for k in unique_k
    }
    sorted_clusters = sorted(cluster_score, key=lambda k: cluster_score[k])
    loser_cluster  = sorted_clusters[0]
    winner_cluster = sorted_clusters[-1]

    winner_idx = np.where(labels == winner_cluster)[0]
    loser_idx  = np.where(labels == loser_cluster)[0]

    P = np.zeros((2, n))
    P[0, winner_idx] =  1.0 / len(winner_idx)   # long view
    P[1, loser_idx]  = -1.0 / len(loser_idx)    # short view (trong universe)

    if mu_posterior is not None:
        q = np.array([
            mu_posterior[winner_idx].mean(),
            mu_posterior[loser_idx].mean(),
        ])
    else:
        q = np.array([
            feat["mom_z"].values[winner_idx].mean(),
            feat["mom_z"].values[loser_idx].mean(),
        ])

    return P, q
