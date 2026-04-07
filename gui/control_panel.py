"""左侧控制面板 — 日期筛选、图表选择、站点筛选、操作按钮"""

import json
import tkinter as tk
from tkinter import ttk

from config import STATIONS_FILE
from gui.styles import COLORS, FONT_BODY, FONT_HEADING


class ControlPanel(ttk.Frame):
    """左侧控制面板"""

    def __init__(self, parent, on_change=None, on_api_fetch=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change
        self._on_api_fetch = on_api_fetch
        self._station_names = self._load_stations()
        self._build_ui()

    def _load_stations(self) -> list[str]:
        with open(STATIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return [s["name"] for s in data["stations"]]

    def _build_ui(self):
        pad = {"padx": 8, "pady": 3}

        # ── 日期范围 ──
        ttk.Label(self, text="日期范围", font=FONT_HEADING).pack(anchor="w", **pad, pady=(10, 3))
        self.day_type_var = tk.StringVar(value="全部")
        for label in ("全部", "工作日", "周末"):
            ttk.Radiobutton(
                self, text=label, variable=self.day_type_var,
                value=label, command=self._fire_change,
            ).pack(anchor="w", padx=16)

        ttk.Separator(self, orient="horizontal").pack(fill="x", **pad, pady=8)

        # ── 图表类型 ──
        ttk.Label(self, text="图表类型", font=FONT_HEADING).pack(anchor="w", **pad)
        self.chart_var = tk.StringVar(value="热力图")
        chart_types = ["热力图", "折线图", "柱状图", "预测图"]
        for ct in chart_types:
            ttk.Radiobutton(
                self, text=ct, variable=self.chart_var,
                value=ct, command=self._fire_change,
            ).pack(anchor="w", padx=16)

        ttk.Separator(self, orient="horizontal").pack(fill="x", **pad, pady=8)

        # ── 站点筛选 ──
        ttk.Label(self, text="站点筛选", font=FONT_HEADING).pack(anchor="w", **pad)

        # 全选/反选
        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor="w", padx=16)
        ttk.Button(btn_frame, text="全选", width=5,
                   command=self._select_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="清空", width=5,
                   command=self._clear_all).pack(side="left", padx=2)

        # 站点列表（用 Canvas+Frame 实现滚动）
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=4)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0, width=180)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self._stations_frame = ttk.Frame(canvas)

        self._stations_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._stations_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.station_vars: dict[str, tk.BooleanVar] = {}
        for name in self._station_names:
            var = tk.BooleanVar(value=True)
            self.station_vars[name] = var
            ttk.Checkbutton(
                self._stations_frame, text=name, variable=var,
                command=self._fire_change,
            ).pack(anchor="w")

        ttk.Separator(self, orient="horizontal").pack(fill="x", **pad, pady=8)

        # ── 操作按钮 ──
        ttk.Button(self, text="刷新图表", command=self._fire_change).pack(
            fill="x", **pad, pady=2)
        ttk.Button(self, text="API 获取数据", command=self._fire_api).pack(
            fill="x", **pad, pady=2)

    def get_filters(self) -> dict:
        """获取当前筛选条件"""
        selected = [name for name, var in self.station_vars.items() if var.get()]
        return {
            "day_type": self.day_type_var.get(),
            "chart_type": self.chart_var.get(),
            "stations": selected if len(selected) < len(self._station_names) else None,
        }

    def _select_all(self):
        for var in self.station_vars.values():
            var.set(True)
        self._fire_change()

    def _clear_all(self):
        for var in self.station_vars.values():
            var.set(False)
        self._fire_change()

    def _fire_change(self):
        if self._on_change:
            self._on_change()

    def _fire_api(self):
        if self._on_api_fetch:
            self._on_api_fetch()
