"""Tkinter 主窗口 — 三栏布局、事件分发、数据流协调"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import OUTPUT_DIR
from gui.styles import (COLORS, FONT_BODY, FONT_HEADING, FONT_TITLE,
                         WINDOW_MIN, WINDOW_SIZE)
from gui.control_panel import ControlPanel
from gui.dashboard_frame import DashboardFrame
from gui.report_panel import ReportPanel
from modules.analyzer import (calc_statistics, detect_lowest_efficiency_period,
                                detect_most_crowded_station, find_bottleneck_periods)
from modules.data_loader import filter_data
from modules.visualizer import (plot_heatmap, plot_ontime_bar, plot_prediction,
                                 plot_speed_trend)


class App(tk.Tk):
    """主应用窗口"""

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.title("城市脉搏 - 公共交通效率分析与优化建议生成器")
        self.geometry(WINDOW_SIZE)
        self.minsize(*WINDOW_MIN)
        self.configure(bg=COLORS["bg_main"])

        self._df_full = df
        self._predictions = None
        self._suggestions: list[str] = []

        self._build_ui()
        self.after(100, self._refresh_all)

    def _build_ui(self):
        # ── 标题栏 ──
        title_bar = tk.Frame(self, bg=COLORS["bg_title"], height=50)
        title_bar.pack(side=tk.TOP, fill=tk.X)
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text="城市脉搏 - 公共交通效率分析与优化建议生成器",
                 font=FONT_TITLE, bg=COLORS["bg_title"],
                 fg=COLORS["text_title"]).pack(side=tk.LEFT, padx=15)

        # 导出按钮
        btn_frame = tk.Frame(title_bar, bg=COLORS["bg_title"])
        btn_frame.pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_frame, text="导出报告", command=self._export_report,
                  bg="#ffffff", fg=COLORS["text_primary"],
                  relief="flat", padx=8).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="导出图表", command=self._export_chart,
                  bg="#ffffff", fg=COLORS["text_primary"],
                  relief="flat", padx=8).pack(side=tk.RIGHT, padx=4)

        # ── 状态栏 ──
        self.status_bar = tk.Label(
            self, text="就绪", font=FONT_BODY, anchor="w",
            bg=COLORS["border"], fg=COLORS["text_secondary"],
            padx=10, pady=2)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # ── 三栏布局 ──
        self.paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashwidth=4,
            bg=COLORS["border"])
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 左侧控制面板
        self.control = ControlPanel(
            self.paned,
            on_change=self._refresh_all,
            on_api_fetch=self._on_api_fetch,
        )
        self.paned.add(self.control, minsize=180, width=220)

        # 中间图表区
        self.dashboard = DashboardFrame(
            self.paned,
            on_hour_change=self._on_hour_change,
        )
        self.dashboard._on_thumb_click_callback = self._on_thumb_click
        self.paned.add(self.dashboard, minsize=400)

        # 右侧报告面板
        self.report = ReportPanel(self.paned)
        self.paned.add(self.report, minsize=220, width=280)

    def _get_filtered_df(self) -> pd.DataFrame:
        """根据控制面板条件筛选数据"""
        filters = self.control.get_filters()
        return filter_data(
            self._df_full,
            day_type=filters["day_type"],
            stations=filters["stations"],
        )

    def _refresh_all(self):
        """刷新所有图表和报告"""
        df = self._get_filtered_df()
        if df.empty:
            self._set_status("无匹配数据，请调整筛选条件")
            return

        filters = self.control.get_filters()
        chart_type = filters["chart_type"]
        hour = self.dashboard.get_current_hour()

        # 更新主图表
        self._draw_main_chart(df, chart_type, hour)

        # 更新缩略图
        self._draw_thumbnails(df, hour)

        # 更新报告
        self._update_report(df)

        self._set_status(
            f"数据已加载 | {len(df)} 条记录 | "
            f"最后更新: {datetime.now().strftime('%H:%M:%S')}")

    def _draw_main_chart(self, df, chart_type: str, hour: int):
        """绘制主图表"""
        fig = self.dashboard.fig
        if chart_type == "热力图":
            plot_heatmap(df, fig, highlight_hour=hour)
        elif chart_type == "折线图":
            plot_speed_trend(df, fig, highlight_hour=hour)
        elif chart_type == "柱状图":
            plot_ontime_bar(df, fig, highlight_hour=hour)
        elif chart_type == "预测图":
            plot_prediction(df, fig, self._predictions)
        self.dashboard.refresh_canvas()

    def _draw_thumbnails(self, df, hour: int):
        """绘制底部缩略图"""
        thumb_map = {
            "热力图": plot_heatmap,
            "折线图": plot_speed_trend,
            "柱状图": plot_ontime_bar,
        }
        for name, plot_fn in thumb_map.items():
            fig, _ = self.dashboard.thumb_figs[name]
            plot_fn(df, fig, highlight_hour=hour)
            self.dashboard.refresh_thumb(name)

    def _update_report(self, df):
        """更新右侧报告"""
        stats = calc_statistics(df)
        crowded = detect_most_crowded_station(df)
        inefficient = detect_lowest_efficiency_period(df)
        bottlenecks = find_bottleneck_periods(df)

        # 结论先行
        from modules.report_generator import generate_conclusion, generate_suggestions
        conclusion = generate_conclusion(stats, crowded, inefficient)
        self.report.update_conclusion(conclusion)

        self.report.update_statistics(stats)
        self.report.update_anomaly(crowded, inefficient)

        # 生成建议
        self._suggestions = generate_suggestions(
            stats, crowded, inefficient, bottlenecks)
        self.report.update_suggestions(self._suggestions)

        # 当前关注时段摘要
        hour = self.dashboard.get_current_hour()
        self._update_hour_summary(df, hour)

        # API 校验对比（仅当有 API 数据时显示）
        from modules.data_loader import compare_sim_vs_api
        comparison = compare_sim_vs_api(df)
        self._api_comparison = comparison
        if comparison:
            self.report.update_api_comparison(
                f"模拟 {comparison['overall_sim_speed']} vs "
                f"API {comparison['overall_api_speed']} km/h  "
                f"偏差 {comparison['overall_diff']:+.1f} km/h",
                f"偏差>20%站点: {', '.join(comparison['warning_stations'])}"
                if comparison["warning_stations"] else "所有站点偏差在合理范围内",
            )
        else:
            self.report.update_api_comparison("", "")

        # 预测：仅在用户选择预测图时触发（MVP 边界）
        filters = self.control.get_filters()
        if filters["chart_type"] == "预测图":
            self._train_and_show_prediction(df)

    def _update_hour_summary(self, df, hour: int):
        """更新当前关注时段摘要"""
        hour_df = df[df["hour"] == hour]
        if hour_df.empty:
            self.report.update_hour_summary(hour, "该时段无数据")
            return
        total_passengers = int(hour_df["passengers"].sum())
        avg_crowding = round(float(hour_df["crowding_level"].mean()), 3)
        avg_delay = round(float(hour_df["delay_minutes"].mean()), 2)
        avg_speed = round(float(hour_df["avg_speed_kmh"].mean()), 1)
        on_time_pct = round(float(hour_df["on_time"].mean() * 100), 1)
        # 该时段最拥堵站点
        busiest = hour_df.groupby("station")["crowding_level"].mean()
        busiest_station = busiest.idxmax()
        busiest_val = round(float(busiest.max()), 3)
        self.report.update_hour_summary(
            hour,
            f"总客流 {total_passengers:,}  拥挤度 {avg_crowding}\n"
            f"延误 {avg_delay}min  车速 {avg_speed}km/h\n"
            f"准点率 {on_time_pct}%\n"
            f"最拥堵: {busiest_station}({busiest_val})",
        )

    def _train_and_show_prediction(self, df):
        """训练预测模型并更新 UI"""
        from modules.predictor import train_passenger_model
        model_info = train_passenger_model(df)
        self._predictions = self._build_prediction_data(df, model_info)
        self.report.update_prediction(
            f"训练 {model_info['train_days']}天  验证 {model_info['test_day']}",
            f"训练R²={model_info['train_r2']}  "
            f"验证R²={model_info['test_r2']}  "
            f"MAE={model_info['test_mae']}")

    def _build_prediction_data(self, df, model_info) -> dict:
        """构建预测图数据"""
        from modules.predictor import predict_next_hour

        hourly = df.groupby("hour")["passengers"].mean()
        hours = list(hourly.index)
        actual = list(hourly.values)
        predicted = []
        for h in hours:
            p = predict_next_hour(model_info, h, 6, True, int(hourly.get(h, 0)))
            predicted.append(p)
        return {"hours": hours, "actual": actual, "predicted": predicted}

    def _on_hour_change(self, hour: int):
        """时间滑块松开后回调"""
        self._refresh_all()

    def _on_thumb_click(self, chart_name: str):
        """缩略图点击回调"""
        self.control.chart_var.set(chart_name)
        self._refresh_all()

    def _on_api_fetch(self):
        """API 获取数据"""
        from config import AMAP_API_KEY
        if not AMAP_API_KEY:
            messagebox.showinfo("提示",
                                "请在 config.py 中填入高德地图 API Key\n"
                                "AMAP_API_KEY = \"你的Key\"")
            return
        try:
            from modules.amap_client import AmapClient
            client = AmapClient(AMAP_API_KEY)
            self._set_status("正在从高德 API 获取数据...")
            self.update()
            # 实际获取逻辑
            from modules.data_loader import merge_api_data
            import json
            with open(str(Path(__file__).parent.parent / "data" / "stations.json"),
                      encoding="utf-8") as f:
                stations = json.load(f)["stations"]
            speeds = client.fetch_line_speeds(stations)
            if speeds:
                self._df_full = merge_api_data(self._df_full, speeds)
                self._refresh_all()
                self._set_status("API 数据已合并到分析链路")
            else:
                self._set_status("API 未返回有效数据，使用内置数据")
        except Exception as e:
            self._set_status(f"API 获取失败: {e}")

    def _export_chart(self):
        """导出当前图表为 PNG"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = OUTPUT_DIR / f"chart_{ts}.png"
        self.dashboard.fig.savefig(str(filepath), dpi=150, bbox_inches="tight")
        self._set_status(f"图表已导出: {filepath.name}")

    def _export_report(self):
        """导出分析报告为 TXT"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = OUTPUT_DIR / f"report_{ts}.txt"

        try:
            from modules.report_generator import (
                generate_conclusion, generate_summary, generate_api_comparison)
            from modules.data_loader import compare_sim_vs_api
            df = self._get_filtered_df()
            stats = calc_statistics(df)
            crowded = detect_most_crowded_station(df)
            inefficient = detect_lowest_efficiency_period(df)
            conclusion = generate_conclusion(stats, crowded, inefficient)
            summary = generate_summary(stats, crowded, inefficient)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"【分析结论】\n{conclusion}\n\n")
                f.write(summary)
                f.write("\n\n【优化建议】\n")
                for i, s in enumerate(self._suggestions, 1):
                    f.write(f"{i}. {s}\n")
                # API 对比段落（如果有 API 数据）
                comparison = compare_sim_vs_api(df)
                api_text = generate_api_comparison(comparison)
                if api_text:
                    f.write(f"\n{api_text}\n")

            self._set_status(f"报告已导出: {filepath.name}")
        except Exception as e:
            self._set_status(f"报告导出失败: {e}")

    def _set_status(self, text: str):
        """更新状态栏"""
        self.status_bar.config(text=text)
