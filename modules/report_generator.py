"""报告生成器 — 文字总结 + 3条优化建议"""

from datetime import datetime


def generate_conclusion(stats: dict, crowded: dict, inefficient: dict) -> str:
    """生成一句结论摘要，评委一眼看懂当前最大问题"""
    rate = stats["on_time_rate"]
    if rate < 90:
        return (
            f"⚠ 整体准点率 {rate}%，低于 90% 标准。"
            f"{inefficient['time_range']} 效率最低"
            f"（延误 {inefficient['avg_delay']}min），"
            f"{crowded['station']}站最拥堵"
            f"（拥挤度 {crowded['avg_crowding']}）。"
        )
    return (
        f"✓ 整体准点率 {rate}%，达到行业标准。"
        f"重点关注{crowded['station']}站拥堵"
        f"（拥挤度 {crowded['avg_crowding']}）"
        f"和 {inefficient['time_range']} 延误"
        f"（{inefficient['avg_delay']}min）。"
    )


def generate_summary(stats: dict, crowded: dict, inefficient: dict) -> str:
    """生成数据分析文字总结"""
    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  城市脉搏 · 公共交通效率分析报告
  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【数据概览】
  分析时段: {stats['date_range']}
  总记录数: {stats['total_records']} 条
  总客流量: {stats['total_passengers']:,} 人次
  整体准点率: {stats['on_time_rate']}%
  平均延误: {stats['avg_delay']} 分钟
  平均车速: {stats['avg_speed']} km/h
  客流高峰时段: {stats['peak_hour']}:00

【异常检测结果】
  ⚠ 最拥堵站点: {crowded['station']}
    - 平均拥挤度: {crowded['avg_crowding']}
    - 峰值拥挤度: {crowded['max_crowding']}
    - 总客流: {crowded['total_passengers']:,} 人次

  ⚠ 最低效时段: {inefficient['time_range']}
    - 平均延误: {inefficient['avg_delay']} 分钟
    - 平均车速: {inefficient['avg_speed']} km/h
    - 低效指数: {inefficient['inefficiency_score']}
"""


def generate_suggestions(
    stats: dict, crowded: dict, inefficient: dict, bottlenecks: list[dict],
) -> list[str]:
    """基于分析结果生成 3 条具体优化建议

    每条建议必须包含至少一个具体指标（站名/时段/准点率/延误/车速）
    """
    suggestions = []
    avg_delay = stats["avg_delay"]
    avg_speed = stats["avg_speed"]

    # 建议1：针对最拥堵站点 — 引用峰值拥挤度和总客流
    peak_hour = stats["peak_hour"]
    suggestions.append(
        f"{crowded['station']}站平均拥挤度 {crowded['avg_crowding']}、"
        f"峰值达 {crowded['max_crowding']}，"
        f"日均承载 {crowded['total_passengers'] // 7:,} 人次。"
        f"建议在 {peak_hour}:00 高峰时段增开 1 班区间车分流，"
        f"并增设临时疏导人员。"
    )

    # 建议2：针对最低效时段 — 与全天均值对比
    delay_ratio = round(inefficient["avg_delay"] / avg_delay, 1) if avg_delay > 0 else 0
    speed_gap = round(avg_speed - inefficient["avg_speed"], 1)
    reduction_target = round(inefficient["avg_delay"] - avg_delay, 1)
    suggestions.append(
        f"{inefficient['time_range']} 时段延误 {inefficient['avg_delay']}min，"
        f"是全天均值的 {delay_ratio} 倍"
        f"（全天均值 {avg_delay}min）；"
        f"车速 {inefficient['avg_speed']}km/h，"
        f"比全天低 {speed_gap}km/h。"
        f"建议优化信号调度，目标降低延误 {reduction_target}min。"
    )

    # 建议3：针对准点率+瓶颈 — 引用具体车速差
    if stats["on_time_rate"] < 90:
        bn = bottlenecks[0] if bottlenecks else None
        if bn:
            speed_diff = round(avg_speed - bn["avg_speed"], 1)
            suggestions.append(
                f"整体准点率 {stats['on_time_rate']}%，低于 90% 标准。"
                f"全线最慢区段: {bn['station']}站 {bn['hour']}:00，"
                f"车速 {bn['avg_speed']}km/h，"
                f"比全天均值低 {speed_diff}km/h。"
                f"建议重点排查该站点时段的运行瓶颈。"
            )
        else:
            suggestions.append(
                f"整体准点率 {stats['on_time_rate']}%，"
                f"低于 90% 标准，建议全线优化调度。"
            )
    else:
        suggestions.append(
            f"整体准点率 {stats['on_time_rate']}% 达到行业标准。"
            f"建议在周末客流较低时段（日均客流较工作日下降约 30%）"
            f"适当减少发车频次，优化运营成本。"
        )

    return suggestions


def generate_api_comparison(comparison: dict) -> str:
    """生成模拟数据 vs API 实际数据的对比段落

    参数 comparison 来自 data_loader.compare_sim_vs_api() 的返回值
    """
    if comparison is None:
        return ""

    lines = [
        "",
        "【模拟 vs API 静态基准车速对比（高德 API）】",
        "  说明: API 返回路径规划静态区间车速（不区分时段），",
        "        下表展示各小时模拟均速偏离 API 基准的程度。",
        f"  模拟平均车速: {comparison['overall_sim_speed']} km/h",
        f"  API 基准车速: {comparison['overall_api_speed']} km/h",
        f"  整体偏差: {comparison['overall_diff']:+.1f} km/h",
        f"  偏差超 20% 站点数: {comparison['warning_count']} 个",
    ]

    if comparison["warning_stations"]:
        lines.append(f"  ⚠ 偏差警告站点: {', '.join(comparison['warning_stations'])}")

    # 各小时偏离明细
    hourly = comparison["hourly"]
    lines.append("")
    lines.append("  时段  模拟均速  API基准  偏差    偏差%")
    for hour, row in hourly.iterrows():
        lines.append(
            f"  {hour:02d}:00  {row['sim_speed']:>6.1f}  "
            f"{row['api_baseline']:>6.1f}  {row['diff']:>+5.1f}  "
            f"{row['deviation_pct']:>5.1f}%"
        )

    return "\n".join(lines)
