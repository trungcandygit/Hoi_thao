#!/usr/bin/env python3
"""
main.py — điểm vào để chạy toàn bộ pipeline BL-K_IO VN30.

Sử dụng:
  python main.py                          # chạy full pipeline với config.yaml
  python main.py --config my_config.yaml  # dùng config tùy chỉnh
  python main.py --skip-robustness        # bỏ qua phân tích robustness
  python main.py --force-reload           # tải lại dữ liệu (bỏ cache)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import load_config, setup_logging
from src.data_loader import DataLoader
from src.backtest import run_backtest
from src.metrics import compute_all_metrics, pairwise_sharpe_tests
from src.robustness import monte_carlo_q, param_sweep
from src.visualization import (
    plot_cumulative_returns,
    plot_drawdown,
    plot_mc_distribution,
    plot_metrics_table,
    plot_robustness_heatmap,
)

logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(description="BL-K_IO VN30 Pipeline")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--skip-robustness", action="store_true")
    p.add_argument("--force-reload",    action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    cfg  = load_config(args.config)
    setup_logging(cfg.get("log_level", "INFO"))

    np.random.seed(cfg.get("random_seed", 42))

    root    = Path(cfg["root_dir"])
    results = root / "results"
    results.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Tải dữ liệu
    # ------------------------------------------------------------------
    loader  = DataLoader(cfg)
    prices  = loader.load_prices(force_reload=args.force_reload)
    mcap    = loader.load_market_cap(force_reload=args.force_reload)
    rf      = loader.load_risk_free()

    logger.info("Giá: %s  |  Market cap: %s", prices.shape, mcap.shape)
    loader.coverage_report(prices)

    # ------------------------------------------------------------------
    # 2. Backtest chính
    # ------------------------------------------------------------------
    m = cfg["model"]
    k_range = tuple(m["n_clusters_range"])
    tau_cfg = m["tau"] if m["tau"] is not None else 1.0 / m["estimation_window"]

    oos_returns, weights_log = run_backtest(
        prices=prices,
        market_cap=mcap,
        rf_series=rf,
        estimation_window=m["estimation_window"],
        k_range=k_range,
        max_weight=m["max_weight"],
        min_weight=m["min_weight"],
        delta=m["delta"],
        omega_type=m["omega_type"],
        tc_bps=m["tc_bps"],
        seed=cfg.get("random_seed", 42),
    )

    oos_returns.to_csv(results / "oos_returns.csv")
    weights_log.to_csv(results / "weights_log.csv")
    logger.info("Đã lưu OOS returns và weights log.")

    # ------------------------------------------------------------------
    # 3. Tính chỉ số hiệu suất
    # ------------------------------------------------------------------
    sub_periods = cfg.get("sub_periods", {})
    metrics = compute_all_metrics(oos_returns, rf, sub_periods=sub_periods)
    metrics.to_csv(results / "metrics.csv", index=False)
    logger.info("\n=== PERFORMANCE METRICS (FULL PERIOD) ===\n%s",
                metrics[metrics["period"] == "full"].to_string(index=False))

    # Kiểm định Sharpe
    sharpe_tests = pairwise_sharpe_tests(
        oos_returns,
        baseline="BL_K_IO",
        n_boot=5000,
        seed=cfg.get("random_seed", 42),
    )
    sharpe_tests.to_csv(results / "sharpe_tests.csv", index=False)
    logger.info("\n=== SHARPE DIFFERENCE TESTS ===\n%s", sharpe_tests.to_string(index=False))

    # ------------------------------------------------------------------
    # 4. Biểu đồ
    # ------------------------------------------------------------------
    plot_cumulative_returns(
        oos_returns,
        out_path=results / "cumulative_returns.png",
        sub_periods=sub_periods,
    )
    plot_drawdown(oos_returns, out_path=results / "drawdown.png")
    plot_metrics_table(metrics, out_path=results / "metrics_table.png", period="full")
    if sub_periods:
        for p_name in sub_periods:
            plot_metrics_table(metrics, out_path=results / f"metrics_table_{p_name}.png",
                               period=p_name)

    # ------------------------------------------------------------------
    # 5. Robustness (tùy chọn)
    # ------------------------------------------------------------------
    if not args.skip_robustness:
        rob_cfg = cfg.get("robustness", {})

        logger.info("=== PARAM SWEEP ===")
        sweep_df = param_sweep(
            prices, mcap, rf,
            estimation_windows=rob_cfg.get("estimation_windows", [36]),
            max_weights=rob_cfg.get("max_weights", [0.30]),
            k_values=rob_cfg.get("k_values", [3]),
            base_cfg=cfg,
            seed=cfg.get("random_seed", 42),
        )
        sweep_df.to_csv(results / "robustness_sweep.csv", index=False)
        plot_robustness_heatmap(sweep_df, out_path=results / "heatmap_sweep.png")

        logger.info("=== MONTE CARLO ===")
        mc_df = monte_carlo_q(
            prices, mcap, rf,
            perturbations=rob_cfg.get("mc_perturbations", [0.05, 0.10]),
            n_scenarios=rob_cfg.get("mc_scenarios", 200),   # giảm khi test
            base_cfg=cfg,
            seed=cfg.get("random_seed", 42),
        )
        mc_df.to_csv(results / "mc_robustness.csv", index=False)
        plot_mc_distribution(mc_df, out_path=results / "mc_distribution.png")
        logger.info("\n=== MONTE CARLO RESULTS ===\n%s", mc_df.to_string(index=False))

    logger.info("Pipeline hoàn thành. Kết quả lưu tại: %s", results)


if __name__ == "__main__":
    main()
