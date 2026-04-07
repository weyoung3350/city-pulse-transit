"""统计分析与异常检测 — 计算指标、找最拥堵站点、最低效时段、瓶颈站点时段"""

import pandas as pd

from config import BASE_SPEED_KMH


def calc_statistics(df: pd.DataFrame) -> dict:
    """计算整体统计指标"""
    return {
        "total_records": len(df),
        "date_range": f"{df['date'].min().date()} ~ {df['date'].max().date()}",
        "total_passengers": int(df["passengers"].sum()),
        "avg_delay": round(df["delay_minutes"].mean(), 2),
        "avg_speed": round(df["avg_speed_kmh"].mean(), 1),
        "on_time_rate": round(df["on_time"].mean() * 100, 1),
        "peak_hour": int(df.groupby("hour")["passengers"].sum().idxmax()),
    }


def detect_most_crowded_station(df: pd.DataFrame) -> dict:
    """找出最拥堵站点：按平均拥挤度排序"""
    station_stats = df.groupby("station").agg(
        avg_crowding=("crowding_level", "mean"),
        max_crowding=("crowding_level", "max"),
        total_passengers=("passengers", "sum"),
    ).sort_values("avg_crowding", ascending=False)

    top = station_stats.iloc[0]
    return {
        "station": station_stats.index[0],
        "avg_crowding": round(float(top["avg_crowding"]), 3),
        "max_crowding": round(float(top["max_crowding"]), 3),
        "total_passengers": int(top["total_passengers"]),
    }


def detect_lowest_efficiency_period(df: pd.DataFrame) -> dict:
    """找出最低效时段

    算法：
    1. 按 hour 聚合，计算平均延误和平均车速
    2. 延误归一化 + 车速损失归一化
    3. 效率得分 = 0.6 × 延误归一化 + 0.4 × 车速损失归一化
    """
    hourly = df.groupby("hour").agg(
        avg_delay=("delay_minutes", "mean"),
        avg_speed=("avg_speed_kmh", "mean"),
    )

    # 延误归一化
    d_min, d_max = hourly["avg_delay"].min(), hourly["avg_delay"].max()
    d_range = d_max - d_min
    hourly["delay_norm"] = (
        (hourly["avg_delay"] - d_min) / d_range if d_range > 0 else 0
    )

    # 车速损失归一化
    hourly["speed_loss"] = BASE_SPEED_KMH - hourly["avg_speed"]
    sl_min, sl_max = hourly["speed_loss"].min(), hourly["speed_loss"].max()
    sl_range = sl_max - sl_min
    hourly["loss_norm"] = (
        (hourly["speed_loss"] - sl_min) / sl_range if sl_range > 0 else 0
    )

    # 综合效率得分
    hourly["inefficiency"] = hourly["delay_norm"] * 0.6 + hourly["loss_norm"] * 0.4
    worst_hour = hourly["inefficiency"].idxmax()

    return {
        "hour": int(worst_hour),
        "time_range": f"{worst_hour}:00 - {worst_hour + 1}:00",
        "avg_delay": round(float(hourly.loc[worst_hour, "avg_delay"]), 2),
        "avg_speed": round(float(hourly.loc[worst_hour, "avg_speed"]), 1),
        "inefficiency_score": round(float(hourly.loc[worst_hour, "inefficiency"]), 3),
    }


def find_bottleneck_periods(df: pd.DataFrame, top_n: int = 3) -> list[dict]:
    """找出瓶颈站点时段 Top N：按站点×时段的最低平均车速"""
    segment = df.groupby(["station", "hour"])["avg_speed_kmh"].mean()
    worst = segment.nsmallest(top_n)
    return [
        {"station": station, "hour": int(hour), "avg_speed": round(speed, 1)}
        for (station, hour), speed in worst.items()
    ]
