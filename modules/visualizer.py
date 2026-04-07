"""可视化模块 — 热力图、折线图、柱状图、预测图"""

import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.figure import Figure

from config import FONT_FAMILY, STATIONS_FILE

# 配置中文字体
matplotlib.rcParams["font.sans-serif"] = [FONT_FAMILY, "STHeiti", "SimHei", "Arial"]
matplotlib.rcParams["axes.unicode_minus"] = False

# Google Material 配色
PALETTE = ["#4285f4", "#ea4335", "#fbbc04", "#34a853",
           "#ff6d01", "#46bdc6", "#7baaf7", "#f07b72"]


def _load_station_order() -> list[str]:
    """加载站点顺序"""
    with open(STATIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [s["name"] for s in data["stations"]]


def plot_heatmap(df, fig: Figure, highlight_hour: int | None = None):
    """热力图：各站点在不同时段的拥挤程度

    X轴=小时(6-23), Y轴=站点(按线路顺序), 颜色=平均拥挤度
    """
    fig.clear()
    ax = fig.add_subplot(111)

    station_order = _load_station_order()
    pivot = df.pivot_table(
        values="crowding_level",
        index="station",
        columns="hour",
        aggfunc="mean",
    )
    pivot = pivot.reindex(station_order)

    sns.heatmap(
        pivot, ax=ax, cmap="YlOrRd", vmin=0, vmax=1,
        linewidths=0.5, linecolor="white",
        cbar_kws={"label": "拥挤度", "shrink": 0.8},
        annot=True, fmt=".2f", annot_kws={"size": 7},
    )

    if highlight_hour is not None and highlight_hour in pivot.columns:
        col_idx = list(pivot.columns).index(highlight_hour)
        ax.axvline(x=col_idx, color="#1a73e8", linewidth=2.5, alpha=0.7)
        ax.axvline(x=col_idx + 1, color="#1a73e8", linewidth=2.5, alpha=0.7)

    ax.set_title("各站点分时段拥挤度热力图", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("时段（小时）", fontsize=11)
    ax.set_ylabel("站点", fontsize=11)
    fig.tight_layout()


def plot_speed_trend(df, fig: Figure, highlight_hour: int | None = None):
    """折线图：平均车速随时间变化趋势

    分工作日/周末两条线
    """
    fig.clear()
    ax = fig.add_subplot(111)

    for day_type, label, color in [("workday", "工作日", PALETTE[0]),
                                    ("weekend", "周末", PALETTE[1])]:
        subset = df[df["day_type"] == day_type]
        if subset.empty:
            continue
        hourly_speed = subset.groupby("hour")["avg_speed_kmh"].mean()
        ax.plot(hourly_speed.index, hourly_speed.values,
                marker="o", linewidth=2, markersize=5,
                label=label, color=color)
        ax.fill_between(hourly_speed.index, hourly_speed.values,
                         alpha=0.1, color=color)

    if highlight_hour is not None:
        ax.axvline(x=highlight_hour, color="#5f6368", linestyle="--",
                    linewidth=1.5, alpha=0.7, label=f"关注: {highlight_hour}:00")

    ax.set_title("平均车速随时间变化趋势", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("时段（小时）", fontsize=11)
    ax.set_ylabel("平均车速（km/h）", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(df["hour"].min() - 0.5, df["hour"].max() + 0.5)
    fig.tight_layout()


def plot_ontime_bar(df, fig: Figure, highlight_hour: int | None = None):
    """柱状图：每日准点率对比

    X轴=日期, Y轴=准点率(%), 蓝=工作日/红=周末, 90%目标线
    """
    fig.clear()
    ax = fig.add_subplot(111)

    daily = df.groupby(["date", "day_type"])["on_time"].mean().reset_index()
    daily["on_time_pct"] = daily["on_time"] * 100
    daily["date_str"] = daily["date"].dt.strftime("%m-%d")
    daily = daily.sort_values("date")

    colors = [PALETTE[0] if dt == "workday" else PALETTE[1]
              for dt in daily["day_type"]]

    bars = ax.bar(daily["date_str"], daily["on_time_pct"], color=colors,
                   edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, daily["on_time_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    ax.set_title("每日准点率对比", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("日期", fontsize=11)
    ax.set_ylabel("准点率（%）", fontsize=11)
    ax.set_ylim(0, 105)
    ax.axhline(y=90, color="#34a853", linestyle="--", alpha=0.7, label="目标线 90%")

    # 图例：手动创建工作日/周末图例
    from matplotlib.patches import Patch
    legend_items = [
        Patch(facecolor=PALETTE[0], label="工作日"),
        Patch(facecolor=PALETTE[1], label="周末"),
        plt.Line2D([0], [0], color="#34a853", linestyle="--", label="目标线 90%"),
    ]
    ax.legend(handles=legend_items, fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    # 当前关注时段标注
    if highlight_hour is not None:
        hour_df = df[df["hour"] == highlight_hour]
        if not hour_df.empty:
            hour_rate = hour_df["on_time"].mean() * 100
            ax.set_title(
                f"每日准点率对比（{highlight_hour}:00 时段准点率 {hour_rate:.1f}%）",
                fontsize=13, fontweight="bold", pad=12)

    fig.tight_layout()


def plot_prediction(df, fig: Figure, predictions: dict | None = None):
    """预测图：实际客流 vs 预测客流

    predictions: {"hours": [...], "actual": [...], "predicted": [...]}
    """
    fig.clear()
    ax = fig.add_subplot(111)

    if predictions is None:
        ax.text(0.5, 0.5, "请先训练预测模型", ha="center", va="center",
                fontsize=14, color="#5f6368", transform=ax.transAxes)
        fig.tight_layout()
        return

    hours = predictions["hours"]
    actual = predictions["actual"]
    predicted = predictions["predicted"]

    ax.plot(hours, actual, marker="o", linewidth=2, color=PALETTE[0],
            label="实际客流", markersize=5)
    ax.plot(hours, predicted, marker="s", linewidth=2, color=PALETTE[1],
            linestyle="--", label="预测客流", markersize=5)

    ax.set_title("客流预测 vs 实际", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("时段（小时）", fontsize=11)
    ax.set_ylabel("客流量（人次）", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
