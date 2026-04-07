"""线性回归预测模型 — 预测未来1小时客流趋势"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def train_passenger_model(df: pd.DataFrame) -> dict:
    """训练客流预测模型（前 N-1 天训练，最后 1 天验证）

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

    # 时间切分：前 N-1 天训练，最后 1 天验证
    dates = sorted(df_sorted["date"].unique())
    train_dates = dates[:-1]
    test_date = dates[-1]

    train_df = df_sorted[df_sorted["date"].isin(train_dates)]
    test_df = df_sorted[df_sorted["date"] == test_date]

    X_train = train_df[features].values
    y_train = train_df["passengers"].values
    X_test = test_df[features].values
    y_test = test_df["passengers"].values

    model = LinearRegression()
    model.fit(X_train, y_train)

    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)
    test_mae = float(np.mean(np.abs(y_test - model.predict(X_test))))

    return {
        "model": model,
        "features": features,
        "train_r2": round(train_r2, 4),
        "test_r2": round(test_r2, 4),
        "test_mae": round(test_mae, 1),
        "train_days": len(train_dates),
        "test_day": str(test_date)[:10],
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
