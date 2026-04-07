"""全局配置 — 字体、颜色、路径、API 等集中管理"""

from pathlib import Path
import platform

# ── 路径 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_FILE = DATA_DIR / "metro_sim_data.csv"
STATIONS_FILE = DATA_DIR / "stations.json"

# ── 随机种子（保证数据可复现）────────────────────────
RANDOM_SEED = 42

# ── 高德地图 API（可选，留空则使用内置数据）──────────
AMAP_API_KEY = ""
AMAP_ENABLED = bool(AMAP_API_KEY)
CITY = "杭州"

# ── 中文字体（按平台自动选择）────────────────────────
if platform.system() == "Darwin":
    FONT_FAMILY = "Hiragino Sans GB"
else:
    FONT_FAMILY = "SimHei"

# ── 数据生成参数 ──────────────────────────────────────
NUM_DAYS = 7          # 生成天数（5工作日 + 2周末）
HOUR_START = 6        # 运营起始小时
HOUR_END = 23         # 运营结束小时
BASE_SPEED_KMH = 40   # 基准车速 km/h
DELAY_THRESHOLD = 2.0  # 准点阈值（分钟）

# ── 站点容量 ──────────────────────────────────────────
LARGE_STATION_CAPACITY = 5500   # 大站（火车东站、城站）
NORMAL_STATION_CAPACITY = 4000  # 普通站

# ── 站点客流权重 ──────────────────────────────────────
STATION_WEIGHTS = {
    "火车东站": 1.8,
    "龙翔桥": 1.6,
    "城站": 1.5,
    "西湖文化广场": 1.4,
    "客运中心": 1.3,
    "凤起路": 1.2,
}

LARGE_STATIONS = {"火车东站", "城站"}
