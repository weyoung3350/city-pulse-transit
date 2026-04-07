"""线性回归预测模型 — 预测未来1小时客流趋势"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def train_passenger_model(df: pd.DataFrame) -> dict:
    """训练客流预测模型

    特征: [hour, station_index, is_workday, prev_hour_passengers]
    目标: passengers
    """
    df_sorted = df.sort_values(["date", "station_index", "hour"]).copy()
    df_sorted["is_workday"] = (df_sorted["day_type"] == "workday").astype(int)

    # 前一小时客流作为滞后特征
    df_sorted["prev_passengers"] = df_sorted.groupby(
        ["date", "station"]
    )["passengers"].shift(1).fillna(0)

    features = ["hour", "station_index", "is_workday", "prev_passengers"]
    X = df_sorted[features].values
    y = df_sorted["passengers"].values

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)
    r2 = model.score(X, y)
    mae = float(np.mean(np.abs(y - y_pred)))

    return {
        "model": model,
        "features": features,
        "r2_score": round(r2, 4),
        "mae": round(mae, 1),
    }


def predict_next_hour(
    model_info: dict,
    current_hour: int,
    station_index: int,
    is_workday: bool,
    current_passengers: int,
) -> int:
    """预测下一小时客流量"""
    model = model_info["model"]
    X_new = np.array([[
        current_hour + 1, station_index,
        int(is_workday), current_passengers,
    ]])
    prediction = model.predict(X_new)[0]
    return max(0, int(round(prediction)))
