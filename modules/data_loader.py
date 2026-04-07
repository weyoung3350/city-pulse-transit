"""数据加载与清洗 — CSV 读取、类型转换、缺失值处理、条件筛选"""

import pandas as pd
from pathlib import Path


def load_csv(filepath: str | Path) -> pd.DataFrame:
    """加载 CSV 数据，设置正确的数据类型"""
    df = pd.read_csv(filepath, encoding="utf-8")
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = df["hour"].astype(int)
    df["passengers"] = df["passengers"].astype(int)
    df["delay_minutes"] = df["delay_minutes"].astype(float)
    df["avg_speed_kmh"] = df["avg_speed_kmh"].astype(float)
    df["crowding_level"] = df["crowding_level"].astype(float)
    df["on_time"] = df["on_time"].astype(bool)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """数据清洗：填充缺失值、裁剪异常值"""
    df = df.copy()
    df["passengers"] = df["passengers"].fillna(0).clip(lower=0)
    df["delay_minutes"] = df["delay_minutes"].fillna(0).clip(lower=0, upper=30)
    df["avg_speed_kmh"] = df["avg_speed_kmh"].fillna(35).clip(lower=15, upper=80)
    df["crowding_level"] = df["crowding_level"].fillna(0).clip(lower=0, upper=1)
    return df


def filter_data(
    df: pd.DataFrame,
    day_type: str | None = None,
    stations: list[str] | None = None,
    hour_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """按条件筛选数据，供 GUI 控制面板调用

    参数:
        day_type: "workday" / "weekend" / None(全部)
        stations: 站点名列表，None 表示全部
        hour_range: (起始小时, 结束小时)，None 表示全部
    """
    result = df.copy()
    if day_type and day_type != "全部":
        mapping = {"工作日": "workday", "周末": "weekend"}
        dt = mapping.get(day_type, day_type)
        result = result[result["day_type"] == dt]
    if stations:
        result = result[result["station"].isin(stations)]
    if hour_range:
        result = result[
            (result["hour"] >= hour_range[0]) & (result["hour"] <= hour_range[1])
        ]
    return result


def merge_api_data(sim_df: pd.DataFrame, api_speeds: list[dict]) -> pd.DataFrame:
    """将 API 获取的实际车速数据合并到模拟数据中

    参数:
        api_speeds: [{"from": "临平", "to": "南苑", "api_speed_kmh": 54.0}, ...]
    返回:
        增加 api_speed_kmh 和 speed_diff 列的 DataFrame
    """
    df = sim_df.copy()
    # 建立站点到 API 车速的映射（用 from 站名作为 key）
    speed_map = {item["from"]: item["api_speed_kmh"] for item in api_speeds}
    df["api_speed_kmh"] = df["station"].map(speed_map)
    df["speed_diff"] = df["avg_speed_kmh"] - df["api_speed_kmh"]
    return df
