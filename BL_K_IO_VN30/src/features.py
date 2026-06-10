"""
Tính đặc trưng cho K-means tại mỗi bước cuốn chiếu.

Đặc trưng:
  1. Idiosyncratic momentum (6-1): lợi suất tích lũy tháng t-6 đến t-2
     sau khi loại bỏ beta * r_market (thị trường = VN-Index proxy).
  2. Low-volatility: std lợi suất tháng trong cửa sổ ước lượng.

Cả hai được chuẩn hóa z-score trước khi đưa vào K-means.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Log returns tháng từ adjusted close."""
    return np.log(prices / prices.shift(1))


def _market_proxy(returns: pd.DataFrame, market_weights: pd.Series | None = None) -> pd.Series:
    """
    Trả lại suất thị trường: bình quân có trọng số (nếu có) hoặc equal-weight.
    """
    if market_weights is not None:
        w = market_weights.reindex(returns.columns).fillna(0)
        w_sum = w.sum()
        if w_sum > 0:
            w = w / w_sum
            return returns.dot(w)
    return returns.mean(axis=1)


def idiosyncratic_momentum(
    returns: pd.DataFrame,
    t: int,
    window: int,
    skip_month: int = 1,
    mom_horizon: int = 6,
    market_weights: pd.Series | None = None,
) -> pd.Series:
    """
    Tính idiosyncratic momentum cho mỗi ticker tại bước t.

    Parameters
    ----------
    returns   : log-return DataFrame (index = date, columns = tickers)
    t         : chỉ số tháng kết thúc cửa sổ ước lượng (exclusive)
    window    : độ dài cửa sổ ước lượng (tháng)
    skip_month: bỏ qua 1 tháng gần nhất (reversal avoidance)
    mom_horizon: cửa sổ tính momentum (tháng)
    """
    # Cửa sổ ước lượng: [t-window, t)
    win = returns.iloc[t - window : t]
    r_mkt = _market_proxy(win, market_weights)

    # Ước lượng beta bằng OLS đơn giản (từng mã)
    betas = {}
    for col in win.columns:
        y = win[col].dropna()
        x = r_mkt.loc[y.index]
        if len(y) < 12:
            betas[col] = np.nan
            continue
        slope, _, _, _, _ = stats.linregress(x, y)
        betas[col] = slope

    # Residual returns
    resid = win.copy()
    for col in win.columns:
        b = betas.get(col, np.nan)
        if np.isnan(b):
            resid[col] = np.nan
        else:
            resid[col] = win[col] - b * r_mkt

    # Momentum: t-mom_horizon-skip đến t-skip (tích lũy)
    start_idx = max(0, t - window)          # đảm bảo trong cửa sổ
    mom_end   = t - skip_month              # bỏ qua tháng gần nhất
    mom_start = mom_end - mom_horizon

    if mom_start < start_idx or mom_end <= mom_start:
        return pd.Series(np.nan, index=win.columns)

    sub = resid.iloc[
        mom_start - (t - window) : mom_end - (t - window)
    ]
    return sub.sum(axis=0)


def low_volatility(
    returns: pd.DataFrame,
    t: int,
    window: int,
) -> pd.Series:
    """Độ lệch chuẩn lợi suất trong cửa sổ ước lượng."""
    win = returns.iloc[t - window : t]
    return win.std(ddof=1)


def build_features(
    returns: pd.DataFrame,
    t: int,
    window: int,
    market_weights: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Kết hợp hai đặc trưng và chuẩn hóa z-score.

    Trả DataFrame (index=tickers, columns=['idio_mom','low_vol','mom_z','vol_z']).
    Loại bỏ ticker có NaN ở bất kỳ đặc trưng nào.
    """
    mom = idiosyncratic_momentum(returns, t, window, market_weights=market_weights)
    vol = low_volatility(returns, t, window)

    feat = pd.DataFrame({"idio_mom": mom, "low_vol": vol}).dropna()

    # z-score
    feat["mom_z"] = stats.zscore(feat["idio_mom"], nan_policy="omit")
    feat["vol_z"] = stats.zscore(feat["low_vol"],  nan_policy="omit")

    return feat
