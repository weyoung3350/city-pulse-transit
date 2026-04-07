"""报告生成器 — 文字总结 + 3条优化建议"""

from datetime import datetime


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

    # 建议1：针对最拥堵站点
    if crowded["avg_crowding"] > 0.7:
        suggestions.append(
            f"建议在{crowded['station']}站增设临时疏导人员，"
            f"该站平均拥挤度达{crowded['avg_crowding']}，"
            f"建议在早晚高峰缩短发车间隔至3分钟，"
            f"预计可降低拥挤度15%-20%。"
        )
    else:
        suggestions.append(
            f"{crowded['station']}站为相对最拥堵站点（平均拥挤度{crowded['avg_crowding']}），"
            f"处于可控范围，建议保持当前运力并持续监测。"
        )

    # 建议2：针对最低效时段
    suggestions.append(
        f"在{inefficient['time_range']}时段，"
        f"列车平均延误达{inefficient['avg_delay']}分钟，"
        f"车速仅{inefficient['avg_speed']}km/h，"
        f"建议优化该时段信号调度系统，"
        f"目标将延误控制在1.5分钟以内。"
    )

    # 建议3：针对准点率或瓶颈
    if stats["on_time_rate"] < 90:
        bn = bottlenecks[0] if bottlenecks else None
        if bn:
            suggestions.append(
                f"当前整体准点率为{stats['on_time_rate']}%，"
                f"低于90%的行业标准，"
                f"建议重点排查{bn['station']}站"
                f"在{bn['hour']}:00时的运行瓶颈，"
                f"该站点时段车速仅{bn['avg_speed']}km/h。"
            )
        else:
            suggestions.append(
                f"当前整体准点率为{stats['on_time_rate']}%，"
                f"低于90%的行业标准，建议全线优化调度。"
            )
    else:
        suggestions.append(
            f"整体准点率{stats['on_time_rate']}%达到行业标准，"
            f"建议在周末客流较低时段适当减少发车频次，"
            f"优化运营成本，预计可节约10%-15%的运营开支。"
        )

    return suggestions


def generate_api_comparison(sim_stats: dict, api_stats: dict) -> str:
    """生成模拟数据 vs API 实际数据的对比段落"""
    return f"""
【模拟 vs 实际数据对比】
  模拟平均车速: {sim_stats.get('avg_speed', '—')} km/h
  API 实际车速: {api_stats.get('avg_speed', '—')} km/h
  偏差: {api_stats.get('speed_diff', '—')} km/h
"""
