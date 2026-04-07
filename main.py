#!/usr/bin/env python3
"""城市脉搏 - 公共交通效率分析与优化建议生成器

初中编程竞赛作品
功能：地铁线路运营数据可视化分析 + 异常检测 + 优化建议
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_FILE
from modules.data_generator import generate_if_missing
from modules.data_loader import load_csv, clean_data


def main():
    # 1. 确保模拟数据存在
    generate_if_missing(DATA_FILE)

    # 2. 加载并清洗数据
    df = load_csv(DATA_FILE)
    df = clean_data(df)
    print(f"数据加载完成: {len(df)} 条记录")

    # 3. 启动 GUI
    from gui.app import App
    app = App(df)
    app.mainloop()


if __name__ == "__main__":
    main()
