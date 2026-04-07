"""高德地图 API 客户端 — 获取站间实际行驶时长（可选功能）"""

import time
import requests


class AmapClient:
    """高德地图 Web 服务 API 客户端"""

    BASE_URL = "https://restapi.amap.com/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def search_station(self, station_name: str, city: str = "杭州") -> dict | None:
        """搜索地铁站，返回经纬度信息"""
        params = {
            "key": self.api_key,
            "keywords": f"{station_name}地铁站",
            "city": city,
            "types": "150500",
            "offset": 1,
        }
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/place/text", params=params, timeout=10)
            data = resp.json()
            if data.get("status") == "1" and data.get("pois"):
                poi = data["pois"][0]
                lon, lat = poi["location"].split(",")
                return {
                    "name": station_name,
                    "lon": float(lon),
                    "lat": float(lat),
                }
        except Exception:
            pass
        return None

    def get_transit_duration(
        self, origin: str, destination: str, city: str = "杭州",
    ) -> dict | None:
        """获取站间实际行驶时长和距离"""
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": 0,
        }
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/direction/transit/integrated",
                params=params, timeout=10)
            data = resp.json()
            if data.get("status") == "1" and data.get("route"):
                route = data["route"]
                transits = route.get("transits", [])
                if transits:
                    return {
                        "distance_m": int(route.get("distance", 0)),
                        "duration_sec": int(transits[0].get("duration", 0)),
                    }
        except Exception:
            pass
        return None

    def fetch_line_speeds(self, stations: list[dict]) -> list[dict]:
        """批量获取所有相邻站间的实际行驶时长，转换为平均车速

        返回: [{"from": "临平", "to": "南苑", "duration_sec": 120,
                "distance_m": 1800, "api_speed_kmh": 54.0}, ...]
        """
        results = []
        for i in range(len(stations) - 1):
            s1, s2 = stations[i], stations[i + 1]
            origin = f"{s1['lon']},{s1['lat']}"
            dest = f"{s2['lon']},{s2['lat']}"

            info = self.get_transit_duration(origin, dest)
            if info and info["duration_sec"] > 0:
                speed = (info["distance_m"] / 1000) / (info["duration_sec"] / 3600)
                results.append({
                    "from": s1["name"],
                    "to": s2["name"],
                    "duration_sec": info["duration_sec"],
                    "distance_m": info["distance_m"],
                    "api_speed_kmh": round(speed, 1),
                })
            time.sleep(0.2)  # API 限速保护
        return results

    def fetch_all_stations(
        self, station_names: list[str], city: str = "杭州",
    ) -> list[dict]:
        """批量获取站点坐标"""
        results = []
        for name in station_names:
            info = self.search_station(name, city)
            if info:
                results.append(info)
            time.sleep(0.2)
        return results
