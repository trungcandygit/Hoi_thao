"""
DataLoader — tải và cache dữ liệu giá & market-cap cho rổ VN30.

Thứ tự ưu tiên:
  1. File CSV thủ công trong data/raw/  (ưu tiên tuyệt đối)
  2. vnstock API                        (fallback tự động)

Schema CSV mong đợi
-------------------
prices.csv
  - date       : YYYY-MM-DD  (ngày cuối tháng hoặc ngày giao dịch bất kỳ)
  - ticker     : str         (VD: ACB, VCB …)
  - close      : float       (giá đóng cửa điều chỉnh)

market_cap.csv
  - date       : YYYY-MM-DD
  - ticker     : str
  - market_cap : float       (vốn hóa, đơn vị tùy — nhất quán là được)

vn30_constituents.csv  (tuỳ chọn — tránh survivorship bias)
  - effective_date : YYYY-MM-DD  (ngày kỳ review bắt đầu có hiệu lực)
  - ticker         : str

risk_free.csv  (tuỳ chọn)
  - year : int
  - rate : float  (lãi suất năm, dạng thập phân VD: 0.055 = 5.5%)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _retry(fn, retries: int = 3, delay: float = 2.0):
    """Gọi fn(), retry tối đa `retries` lần với sleep."""
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == retries:
                raise
            logger.warning("Lần thử %d thất bại: %s — thử lại sau %.0fs", attempt + 1, exc, delay)
            time.sleep(delay)
            delay *= 2


# ---------------------------------------------------------------------------
# ConstituentManager — xử lý dynamic basket
# ---------------------------------------------------------------------------

class ConstituentManager:
    """
    Trả về danh sách ticker hợp lệ tại một thời điểm t.

    Nếu không có constituents_file → dùng danh sách fallback (survivorship bias!).
    """

    def __init__(self, constituents_file: Optional[Path], fallback_tickers: List[str]):
        self._dynamic: Optional[pd.DataFrame] = None
        self._fallback = sorted(set(fallback_tickers))

        if constituents_file and Path(constituents_file).exists():
            df = pd.read_csv(constituents_file, parse_dates=["effective_date"])
            df["ticker"] = df["ticker"].str.upper().str.strip()
            df = df.sort_values("effective_date")
            self._dynamic = df
            logger.info("Đã tải dynamic constituents: %d kỳ, %d mã duy nhất",
                        df["effective_date"].nunique(), df["ticker"].nunique())
        else:
            logger.warning(
                "Không tìm thấy %s — dùng danh sách VN30 hiện tại (%d mã). "
                "CÓ THỂ GÂY SURVIVORSHIP BIAS!",
                constituents_file, len(self._fallback),
            )

    def tickers_at(self, date: pd.Timestamp) -> List[str]:
        """Trả danh sách ticker trong rổ VN30 tại `date`."""
        if self._dynamic is None:
            return self._fallback
        # Lấy kỳ review mới nhất có effective_date <= date
        valid = self._dynamic[self._dynamic["effective_date"] <= date]
        if valid.empty:
            return []
        latest_date = valid["effective_date"].max()
        return sorted(valid[valid["effective_date"] == latest_date]["ticker"].tolist())

    def all_tickers(self) -> List[str]:
        """Tất cả mã từng xuất hiện trong mọi kỳ."""
        if self._dynamic is None:
            return self._fallback
        return sorted(self._dynamic["ticker"].unique().tolist())


# ---------------------------------------------------------------------------
# DataLoader
# ---------------------------------------------------------------------------

class DataLoader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.root = Path(cfg.get("root_dir", "."))
        self.raw_dir = self.root / cfg["data"]["raw_dir"]
        self.proc_dir = self.root / cfg["data"]["processed_dir"]
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.proc_dir.mkdir(parents=True, exist_ok=True)

        self.start = pd.Timestamp(cfg["data"]["start_date"])
        self.end   = pd.Timestamp(cfg["data"]["end_date"])
        self.freq  = cfg["data"].get("freq", "ME")

        self.constituents = ConstituentManager(
            constituents_file=self.raw_dir / Path(cfg["data"]["constituents_file"]).name,
            fallback_tickers=cfg["data"].get("vn30_current", []),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_prices(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Trả DataFrame: index = month-end dates, columns = tickers.
        Giá đóng cửa điều chỉnh theo tháng.
        """
        cache = self.proc_dir / "prices_monthly.parquet"
        if cache.exists() and not force_reload:
            logger.info("Đọc giá từ cache: %s", cache)
            return pd.read_parquet(cache)

        prices = self._load_prices_raw()
        prices.to_parquet(cache)
        logger.info("Đã cache giá vào %s", cache)
        return prices

    def load_market_cap(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Trả DataFrame: index = month-end dates, columns = tickers.
        Vốn hóa thị trường theo tháng.
        """
        cache = self.proc_dir / "market_cap_monthly.parquet"
        if cache.exists() and not force_reload:
            logger.info("Đọc market cap từ cache: %s", cache)
            return pd.read_parquet(cache)

        mcap = self._load_mcap_raw()
        mcap.to_parquet(cache)
        logger.info("Đã cache market cap vào %s", cache)
        return mcap

    def load_risk_free(self) -> pd.Series:
        """
        Trả Series: index = year (int), values = annual rate (float).
        """
        rf_file = self.raw_dir / Path(self.cfg["data"]["risk_free_file"]).name
        if rf_file.exists():
            df = pd.read_csv(rf_file)
            df["year"] = df["year"].astype(int)
            return df.set_index("year")["rate"]
        # Fallback: mức bình quân lịch sử TPCP VN 10Y ≈ 5.5%
        logger.warning(
            "Không tìm thấy %s — dùng risk-free cố định 5.5%/năm. "
            "Hãy cấp file để kết quả chính xác hơn.", rf_file
        )
        years = range(self.start.year, self.end.year + 2)
        return pd.Series({y: 0.055 for y in years})

    def coverage_report(self, prices: pd.DataFrame) -> pd.DataFrame:
        """In báo cáo coverage: số tháng dữ liệu mỗi mã."""
        total = len(prices)
        rpt = pd.DataFrame({
            "months_available": prices.notna().sum(),
            "first_date": prices.apply(lambda c: c.first_valid_index()),
            "last_date":  prices.apply(lambda c: c.last_valid_index()),
            "pct_coverage": (prices.notna().sum() / total * 100).round(1),
        }).sort_values("months_available", ascending=False)
        logger.info("\n=== COVERAGE REPORT ===\n%s", rpt.to_string())
        missing = rpt[rpt["pct_coverage"] < 30]
        if not missing.empty:
            logger.warning("Mã có coverage < 30%%:\n%s", missing.index.tolist())
        return rpt

    # ------------------------------------------------------------------
    # Internal — CSV path
    # ------------------------------------------------------------------

    def _load_prices_raw(self) -> pd.DataFrame:
        csv_path = self.raw_dir / Path(self.cfg["data"]["prices_file"]).name
        if csv_path.exists():
            logger.info("Đọc prices từ CSV thủ công: %s", csv_path)
            return self._read_price_csv(csv_path)
        logger.info("Không có CSV thủ công — thử vnstock …")
        return self._fetch_via_vnstock_prices()

    def _load_mcap_raw(self) -> pd.DataFrame:
        csv_path = self.raw_dir / Path(self.cfg["data"]["marketcap_file"]).name
        if csv_path.exists():
            logger.info("Đọc market cap từ CSV thủ công: %s", csv_path)
            return self._read_price_csv(csv_path, value_col="market_cap")
        logger.info("Không có CSV thủ công — thử vnstock …")
        return self._fetch_via_vnstock_mcap()

    # ------------------------------------------------------------------
    # CSV reader
    # ------------------------------------------------------------------

    def _read_price_csv(self, path: Path, value_col: str = "close") -> pd.DataFrame:
        df = pd.read_csv(path, parse_dates=["date"])
        df["ticker"] = df["ticker"].str.upper().str.strip()
        df = df[(df["date"] >= self.start) & (df["date"] <= self.end)]
        pivot = df.pivot_table(index="date", columns="ticker", values=value_col, aggfunc="last")
        pivot.index = pd.DatetimeIndex(pivot.index)
        pivot = pivot.resample(self.freq).last()
        pivot = pivot.loc[self.start:self.end]
        return pivot

    # ------------------------------------------------------------------
    # vnstock fallback
    # ------------------------------------------------------------------

    def _fetch_via_vnstock_prices(self) -> pd.DataFrame:
        tickers = self.constituents.all_tickers()
        frames: Dict[str, pd.Series] = {}
        failed: List[str] = []

        for ticker in tickers:
            try:
                series = _retry(lambda t=ticker: self._vnstock_price_one(t))
                frames[ticker] = series
                logger.info("  ✓ %s  (%d tháng)", ticker, series.notna().sum())
            except Exception as exc:
                logger.error("  ✗ %s: %s", ticker, exc)
                failed.append(ticker)

        if failed:
            logger.warning("Không tải được %d mã: %s", len(failed), failed)
        if not frames:
            raise RuntimeError(
                "Không tải được dữ liệu nào từ vnstock.\n"
                "Hãy cấp file data/raw/prices.csv theo schema đã mô tả trong README."
            )
        df = pd.DataFrame(frames)
        df.index = pd.DatetimeIndex(df.index)
        df = df.resample(self.freq).last()
        df = df.loc[self.start:self.end]
        return df

    def _vnstock_price_one(self, ticker: str) -> pd.Series:
        from vnstock import Vnstock  # lazy import
        stk = Vnstock().stock(symbol=ticker, source="VCI")
        raw = stk.quote.history(
            start=self.start.strftime("%Y-%m-%d"),
            end=self.end.strftime("%Y-%m-%d"),
            interval="1M",
        )
        # vnstock trả cột 'time'/'close' hoặc 'date'/'close'
        date_col = "time" if "time" in raw.columns else "date"
        raw[date_col] = pd.to_datetime(raw[date_col])
        s = raw.set_index(date_col)["close"].rename(ticker)
        s.index = pd.DatetimeIndex(s.index)
        return s

    def _fetch_via_vnstock_mcap(self) -> pd.DataFrame:
        """
        vnstock hiện không cấp market_cap theo tháng trực tiếp.
        Ước tính = shares_outstanding × close price nếu cần.
        Nếu thiếu, trả NaN và cảnh báo.
        """
        prices = self.load_prices()
        tickers = prices.columns.tolist()
        frames: Dict[str, pd.Series] = {}
        failed: List[str] = []

        for ticker in tickers:
            try:
                series = _retry(lambda t=ticker: self._vnstock_mcap_one(t, prices[t]))
                frames[ticker] = series
            except Exception as exc:
                logger.warning("  market_cap %s: %s — dùng NaN", ticker, exc)
                failed.append(ticker)
                frames[ticker] = pd.Series(np.nan, index=prices.index, name=ticker)

        if failed:
            logger.warning(
                "Không lấy được market_cap cho %d mã: %s\n"
                "Fallback: dùng equal-weight market-cap (1/N) cho các mã này.",
                len(failed), failed,
            )
        df = pd.DataFrame(frames)
        return df

    def _vnstock_mcap_one(self, ticker: str, price_series: pd.Series) -> pd.Series:
        from vnstock import Vnstock  # lazy import
        stk = Vnstock().stock(symbol=ticker, source="VCI")
        # Lấy overview để lấy số lượng cổ phiếu lưu hành
        info = stk.company.overview()
        shares = None
        for col in ["outstanding_share", "shares_outstanding", "listed_share"]:
            if col in info.columns:
                shares = float(info[col].iloc[0])
                break
        if shares is None:
            raise ValueError(f"Không tìm thấy cột shares cho {ticker}")
        mcap = price_series * shares
        return mcap.rename(ticker)
