"""右侧报告面板 — 数据概览、异常检测、优化建议、预测结果"""

import tkinter as tk
from tkinter import ttk

from gui.styles import COLORS, FONT_BODY, FONT_HEADING, FONT_SMALL


class ReportPanel(ttk.Frame):
    """右侧分析报告面板"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # 使用 Canvas + Scrollbar 实现滚动
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._content = ttk.Frame(canvas)

        self._content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        pad = {"padx": 8, "pady": 2}

        # ── 数据概览 ──
        self._add_section("数据概览")
        self.lbl_records = self._add_item("总记录数", "—")
        self.lbl_date_range = self._add_item("日期范围", "—")
        self.lbl_passengers = self._add_item("总客流量", "—")
        self.lbl_on_time = self._add_item("准点率", "—")
        self.lbl_avg_delay = self._add_item("平均延误", "—")
        self.lbl_avg_speed = self._add_item("平均车速", "—")
        self.lbl_peak = self._add_item("高峰时段", "—")

        ttk.Separator(self._content, orient="horizontal").pack(fill="x", **pad, pady=6)

        # ── 异常检测 ──
        self._add_section("异常检测")
        self.lbl_crowded = self._add_item("最拥堵站点", "—")
        self.lbl_crowded_detail = self._add_detail()
        self.lbl_inefficient = self._add_item("最低效时段", "—")
        self.lbl_inefficient_detail = self._add_detail()

        ttk.Separator(self._content, orient="horizontal").pack(fill="x", **pad, pady=6)

        # ── 优化建议 ──
        self._add_section("优化建议")
        self.suggestion_labels: list[ttk.Label] = []
        for i in range(3):
            lbl = ttk.Label(self._content, text=f"{i+1}. —", font=FONT_SMALL,
                            wraplength=250, justify="left")
            lbl.pack(anchor="w", padx=12, pady=2)
            self.suggestion_labels.append(lbl)

        ttk.Separator(self._content, orient="horizontal").pack(fill="x", **pad, pady=6)

        # ── 预测结果 ──
        self._add_section("预测结果")
        self.lbl_predict_info = self._add_detail()
        self.lbl_predict_result = self._add_detail()

    def _add_section(self, title: str):
        ttk.Label(self._content, text=title, font=FONT_HEADING).pack(
            anchor="w", padx=8, pady=(8, 2))

    def _add_item(self, label: str, value: str) -> ttk.Label:
        frame = ttk.Frame(self._content)
        frame.pack(anchor="w", padx=12, pady=1, fill="x")
        ttk.Label(frame, text=f"{label}:", font=FONT_BODY, width=10, anchor="w").pack(
            side="left")
        val_lbl = ttk.Label(frame, text=value, font=FONT_BODY)
        val_lbl.pack(side="left", fill="x", expand=True)
        return val_lbl

    def _add_detail(self) -> ttk.Label:
        lbl = ttk.Label(self._content, text="", font=FONT_SMALL,
                        wraplength=250, justify="left", foreground=COLORS["text_secondary"])
        lbl.pack(anchor="w", padx=16, pady=1)
        return lbl

    def update_statistics(self, stats: dict):
        """更新数据概览区域"""
        self.lbl_records.config(text=f"{stats['total_records']}")
        self.lbl_date_range.config(text=stats["date_range"])
        self.lbl_passengers.config(text=f"{stats['total_passengers']:,}")
        self.lbl_on_time.config(text=f"{stats['on_time_rate']}%")
        self.lbl_avg_delay.config(text=f"{stats['avg_delay']} 分钟")
        self.lbl_avg_speed.config(text=f"{stats['avg_speed']} km/h")
        self.lbl_peak.config(text=f"{stats['peak_hour']}:00")

    def update_anomaly(self, crowded: dict, inefficient: dict):
        """更新异常检测区域"""
        self.lbl_crowded.config(text=crowded["station"])
        self.lbl_crowded_detail.config(
            text=f"平均拥挤度: {crowded['avg_crowding']}  "
                 f"峰值: {crowded['max_crowding']}  "
                 f"总客流: {crowded['total_passengers']:,}")

        self.lbl_inefficient.config(text=inefficient["time_range"])
        self.lbl_inefficient_detail.config(
            text=f"平均延误: {inefficient['avg_delay']}min  "
                 f"车速: {inefficient['avg_speed']}km/h  "
                 f"低效指数: {inefficient['inefficiency_score']}")

    def update_suggestions(self, suggestions: list[str]):
        """更新优化建议"""
        for i, lbl in enumerate(self.suggestion_labels):
            if i < len(suggestions):
                lbl.config(text=f"{i+1}. {suggestions[i]}")
            else:
                lbl.config(text=f"{i+1}. —")

    def update_prediction(self, info: str, result: str = ""):
        """更新预测结果"""
        self.lbl_predict_info.config(text=info)
        self.lbl_predict_result.config(text=result)
