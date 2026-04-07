"""中间图表区 — 主图表 + 时间滑块 + 底部缩略图"""

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gui.styles import COLORS, FONT_BODY


class DashboardFrame(ttk.Frame):
    """中间图表展示区"""

    def __init__(self, parent, on_hour_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_hour_change = on_hour_change

        # ── 主图表 ──
        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ── 时间滑块区域 ──
        slider_frame = ttk.Frame(self)
        slider_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(slider_frame, text="时段:", font=FONT_BODY).pack(side=tk.LEFT)
        self.hour_label = ttk.Label(slider_frame, text="6:00", font=FONT_BODY, width=6)
        self.hour_label.pack(side=tk.LEFT)

        self._slider_var = tk.DoubleVar(value=6)
        self.time_slider = ttk.Scale(
            slider_frame, from_=6, to=23, orient=tk.HORIZONTAL,
            variable=self._slider_var,
            command=self._on_slider_drag,
        )
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # release-driven: 松开鼠标才触发图表重绘
        self.time_slider.bind("<ButtonRelease-1>", self._on_slider_release)

        # ── 底部缩略图 ──
        self.thumb_frame = ttk.Frame(self)
        self.thumb_frame.pack(fill=tk.X, padx=5, pady=5)

        self.thumb_figs: dict[str, tuple[Figure, FigureCanvasTkAgg]] = {}
        for name in ("热力图", "折线图", "柱状图"):
            frame = ttk.Frame(self.thumb_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

            fig = Figure(figsize=(2.5, 1.5), dpi=72)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas.get_tk_widget().bind("<Button-1>",
                                         lambda e, n=name: self._on_thumb_click(n))
            self.thumb_figs[name] = (fig, canvas)

            ttk.Label(frame, text=name, font=FONT_BODY, anchor="center").pack()

    def get_current_hour(self) -> int:
        """获取当前滑块选中的小时"""
        return int(self._slider_var.get())

    def _on_slider_drag(self, value):
        """拖动中仅更新标签"""
        hour = int(float(value))
        self.hour_label.config(text=f"{hour}:00")

    def _on_slider_release(self, event):
        """松开后触发回调"""
        if self._on_hour_change:
            self._on_hour_change(self.get_current_hour())

    def _on_thumb_click(self, chart_name: str):
        """点击缩略图切换主图表"""
        if self._on_thumb_click_callback:
            self._on_thumb_click_callback(chart_name)

    _on_thumb_click_callback = None

    def refresh_canvas(self):
        """刷新主图表画布"""
        self.canvas.draw()

    def refresh_thumb(self, name: str):
        """刷新指定缩略图"""
        if name in self.thumb_figs:
            self.thumb_figs[name][1].draw()
