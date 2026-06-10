"""
Vẽ biểu đồ kết quả: cumulative returns, drawdown, robustness heatmap.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns

COLORS = {
    "BL_K_IO": "#1f77b4",
    "BL":      "#ff7f0e",
    "TAN":     "#2ca02c",
    "MKT":     "#d62728",
    "EW":      "#9467bd",
}

LINE_STYLES = {
    "BL_K_IO": "-",
    "BL":      "--",
    "TAN":     "-.",
    "MKT":     ":",
    "EW":      (0, (3, 1, 1, 1)),
}


def plot_cumulative_returns(
    returns: pd.DataFrame,
    out_path: Path,
    title: str = "Cumulative Returns (OOS)",
    sub_periods: Optional[dict] = None,
) -> None:
    cum = (1 + returns).cumprod()
    fig, ax = plt.subplots(figsize=(12, 6))

    for col in cum.columns:
        ax.plot(
            cum.index, cum[col],
            label=col,
            color=COLORS.get(col, None),
            linestyle=LINE_STYLES.get(col, "-"),
            linewidth=1.8,
        )

    if sub_periods:
        for name, rng in sub_periods.items():
            ax.axvspan(
                pd.Timestamp(rng["start"]), pd.Timestamp(rng["end"]),
                alpha=0.06, label=name,
            )

    ax.set_title(title, fontsize=13)
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return (×)")
    ax.legend(loc="upper left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_drawdown(returns: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    for col in returns.columns:
        cum = (1 + returns[col]).cumprod()
        dd  = (cum - cum.cummax()) / cum.cummax()
        ax.fill_between(dd.index, dd, 0,
                        label=col,
                        color=COLORS.get(col, None),
                        alpha=0.4)
        ax.plot(dd.index, dd, color=COLORS.get(col, None), linewidth=0.8)

    ax.set_title("Drawdown Comparison")
    ax.set_ylabel("Drawdown")
    ax.legend(loc="lower left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_metrics_table(
    metrics_df: pd.DataFrame,
    out_path: Path,
    period: str = "full",
) -> None:
    sub = metrics_df[metrics_df["period"] == period].set_index("strategy")
    cols = ["ann_return", "ann_std", "sharpe", "sortino", "max_drawdown"]
    sub = sub[cols].round(4)

    fig, ax = plt.subplots(figsize=(10, max(3, len(sub) * 0.6 + 1)))
    ax.axis("off")
    tbl = ax.table(
        cellText=sub.values,
        rowLabels=sub.index,
        colLabels=cols,
        cellLoc="center",
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.4)
    ax.set_title(f"Performance Metrics — {period}", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_robustness_heatmap(
    sweep_df: pd.DataFrame,
    out_path: Path,
    pivot_x: str = "estimation_window",
    pivot_y: str = "max_weight",
    value: str = "sharpe",
    k_val: Optional[int] = None,
) -> None:
    df = sweep_df.copy()
    if k_val is not None:
        df = df[df["k"] == k_val]
    pivot = df.pivot_table(index=pivot_y, columns=pivot_x, values=value, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        pivot, annot=True, fmt=".2f", cmap="RdYlGn",
        linewidths=0.4, ax=ax,
    )
    ax.set_title(f"Sharpe Heatmap ({pivot_x} × {pivot_y})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_mc_distribution(mc_df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for _, row in mc_df.iterrows():
        label = f"±{row['perturbation']*100:.0f}%"
        ax.bar(label, row["mean_sharpe"],
               yerr=[[row["mean_sharpe"] - row["p5_sharpe"]],
                     [row["p95_sharpe"] - row["mean_sharpe"]]],
               capsize=5, alpha=0.7)
    ax.set_title("Monte Carlo Robustness — BL_K_IO Sharpe Distribution")
    ax.set_ylabel("Sharpe Ratio")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
