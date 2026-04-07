"""模拟数据生成器 — 生成杭州地铁1号线运行数据

运行方式: python modules/data_generator.py
输出文件: data/metro_sim_data.csv（约1764条记录）
"""

import csv
import json
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# 支持直接运行和模块导入两种方式
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    BASE_SPEED_KMH, DATA_DIR, DATA_FILE, DELAY_THRESHOLD, HOUR_END,
    HOUR_START, LARGE_STATION_CAPACITY, LARGE_STATIONS,
    NORMAL_STATION_CAPACITY, NUM_DAYS, RANDOM_SEED, STATIONS_FILE,
    STATION_WEIGHTS,
)


def load_stations() -> list[dict]:
    """加载站点元信息"""
    with open(STATIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["stations"]


def base_passenger_curve(hour: int, day_type: str) -> float:
    """返回 0-1 的归一化客流系数

    工作日：早高峰 8:00 + 晚高峰 18:00 双峰高斯
    周末：白天 12:00 + 下午 17:00 平缓双峰
    """
    if day_type == "workday":
        morning = math.exp(-0.5 * ((hour - 8.0) / 0.8) ** 2)
        evening = math.exp(-0.5 * ((hour - 18.0) / 1.0) ** 2)
        base = max(morning, evening)
        noon = 0.3 * math.exp(-0.5 * ((hour - 12.5) / 1.2) ** 2)
        return max(base, noon, 0.08)
    else:
        mid_day = 0.6 * math.exp(-0.5 * ((hour - 12.0) / 2.5) ** 2)
        afternoon = 0.5 * math.exp(-0.5 * ((hour - 17.0) / 2.0) ** 2)
        return max(mid_day, afternoon, 0.1)


def generate_passengers(hour: int, station_name: str, day_type: str) -> int:
    """生成某站某时段的客流量"""
    curve = base_passenger_curve(hour, day_type)
    weight = STATION_WEIGHTS.get(station_name, 1.0)
    base_max = 5000
    passengers = int(curve * weight * base_max + random.gauss(0, 150))
    return max(50, passengers)


def calc_crowding(passengers: int, station_name: str) -> float:
    """计算拥挤度 (0.0 ~ 1.0)"""
    capacity = (LARGE_STATION_CAPACITY if station_name in LARGE_STATIONS
                else NORMAL_STATION_CAPACITY)
    return min(1.0, round(passengers / capacity, 3))


def generate_delay(passengers: int, hour: int) -> float:
    """生成平均延误（分钟）"""
    base_delay = 0.5
    crowding_factor = (passengers / 5000) * 2.0
    peak_factor = 1.5 if hour in (7, 8, 17, 18) else 0.5
    noise = random.gauss(0, 0.3)
    return round(max(0, base_delay + crowding_factor * peak_factor + noise), 2)


def generate_speed(crowding: float) -> float:
    """生成区间平均车速 (km/h)"""
    speed_reduction = crowding * 12.0
    noise = random.gauss(0, 1.5)
    return round(max(20, BASE_SPEED_KMH - speed_reduction + noise), 1)


def generate_dates() -> list[tuple[date, str]]:
    """生成 7 天日期序列：5 工作日 + 2 周末"""
    start = date(2026, 3, 30)  # 周一
    dates = []
    for i in range(NUM_DAYS):
        d = start + timedelta(days=i)
        day_type = "weekend" if d.weekday() >= 5 else "workday"
        dates.append((d, day_type))
    return dates


def generate_data() -> list[dict]:
    """生成全部模拟数据"""
    random.seed(RANDOM_SEED)
    stations = load_stations()
    dates = generate_dates()
    rows = []

    for d, day_type in dates:
        for hour in range(HOUR_START, HOUR_END + 1):
            for st in stations:
                passengers = generate_passengers(hour, st["name"], day_type)
                crowding = calc_crowding(passengers, st["name"])
                delay = generate_delay(passengers, hour)
                speed = generate_speed(crowding)
                on_time = delay < DELAY_THRESHOLD

                rows.append({
                    "date": d.isoformat(),
                    "day_type": day_type,
                    "hour": hour,
                    "station": st["name"],
                    "station_index": st["index"],
                    "passengers": passengers,
                    "delay_minutes": delay,
                    "avg_speed_kmh": speed,
                    "crowding_level": crowding,
                    "on_time": on_time,
                })
    return rows


def save_csv(rows: list[dict], filepath: Path) -> None:
    """保存数据到 CSV 文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date", "day_type", "hour", "station", "station_index",
        "passengers", "delay_minutes", "avg_speed_kmh",
        "crowding_level", "on_time",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_if_missing(filepath: Path | None = None) -> Path:
    """如果 CSV 不存在则生成，返回文件路径"""
    filepath = filepath or DATA_FILE
    if not filepath.exists():
        rows = generate_data()
        save_csv(rows, filepath)
        print(f"已生成模拟数据: {filepath} ({len(rows)} 条记录)")
    return filepath


if __name__ == "__main__":
    rows = generate_data()
    save_csv(rows, DATA_FILE)
    print(f"已生成模拟数据: {DATA_FILE}")
    print(f"记录数: {len(rows)}")
    print(f"日期范围: {rows[0]['date']} ~ {rows[-1]['date']}")
