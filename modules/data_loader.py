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
    """将 API 获取的实际区间车速合并到模拟数据中

    为每个站点（按 from 站名）挂上 API 基准车速，然后计算：
    - api_speed_kmh: API 返回的区间实际车速
    - speed_diff: 模拟车速 - API 车速
    - speed_deviation_pct: 偏差百分比 |diff| / api_speed × 100
    - api_warning: 偏差超过 20% 时标记为 True
    """
    df = sim_df.copy()
    speed_map = {item["from"]: item["api_speed_kmh"] for item in api_speeds}
    df["api_speed_kmh"] = df["station"].map(speed_map)
    df["speed_diff"] = df["avg_speed_kmh"] - df["api_speed_kmh"]
    df["speed_deviation_pct"] = (
        df["speed_diff"].abs() / df["api_speed_kmh"].replace(0, float("nan")) * 100
    ).round(1)
    df["api_warning"] = df["speed_deviation_pct"] > 20
    return df


def compare_sim_vs_api(df: pd.DataFrame) -> dict | None:
    """模拟各小时均速 vs API 静态基准车速对比

    说明：高德 API 返回的是路径规划的静态区间行驶时长，不区分小时。
    因此 api_speed 在所有小时中是同一个值（按站点），hourly 表展示的是
    "各小时模拟均速偏离 API 静态基准的程度"。

    返回: {"hourly": DataFrame(hour, sim_speed, api_baseline, diff, deviation_pct),
           "overall_sim_speed": float, "overall_api_speed": float,
           "overall_diff": float,
           "warning_count": int (去重站点数),
           "warning_stations": list[str]}
    如果没有 api_speed_kmh 列则返回 None
    """
    if "api_speed_kmh" not in df.columns or df["api_speed_kmh"].isna().all():
        return None

    has_api = df.dropna(subset=["api_speed_kmh"])
    if has_api.empty:
        return None

    hourly = has_api.groupby("hour").agg(
        sim_speed=("avg_speed_kmh", "mean"),
        api_baseline=("api_speed_kmh", "mean"),
    ).round(1)
    hourly["diff"] = (hourly["sim_speed"] - hourly["api_baseline"]).round(1)
    hourly["deviation_pct"] = (
        hourly["diff"].abs() / hourly["api_baseline"].replace(0, float("nan")) * 100
    ).round(1)

    # 警告计数：按站点去重，而非记录条数
    warning_stations = has_api.loc[
        has_api["api_warning"], "station"
    ].unique().tolist()

    return {
        "hourly": hourly,
        "overall_sim_speed": round(float(has_api["avg_speed_kmh"].mean()), 1),
        "overall_api_speed": round(float(has_api["api_speed_kmh"].mean()), 1),
        "overall_diff": round(
            float(has_api["avg_speed_kmh"].mean() - has_api["api_speed_kmh"].mean()), 1),
        "warning_count": len(warning_stations),
        "warning_stations": warning_stations,
    }
