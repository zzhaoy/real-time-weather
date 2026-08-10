"""中央气象台 (nmc.cn) API 客户端"""

import requests
from typing import Optional

BASE_URL = "https://www.nmc.cn/rest"
TIMEOUT = 10


class NmcClient:
    """中央气象台 API 客户端，支持城市查询和天气获取"""

    def __init__(self, timeout: int = TIMEOUT):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Referer": "https://www.nmc.cn/publish/forecast.html",
            }
        )
        self._city_cache: Optional[list[dict]] = None

    def _get(self, path: str, params: dict = None) -> dict | list:
        """发送 GET 请求并返回 JSON"""
        url = f"{BASE_URL}{path}"
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_provinces(self) -> list[dict]:
        """获取所有省份列表"""
        data = self._get("/province")
        return data

    def get_cities(self, province_code: str) -> list[dict]:
        """获取指定省份下的所有城市"""
        return self._get(f"/province/{province_code}")

    def get_all_cities(self, use_cache: bool = True) -> list[dict]:
        """获取全国所有城市列表（含 stationid）

        返回格式: [{"city": "北京", "code": "Wqsps", "province": "北京市", "url": "..."}]
        """
        if use_cache and self._city_cache is not None:
            return self._city_cache

        provinces = self.get_provinces()
        cities: list[dict] = []
        for prov in provinces:
            try:
                prov_cities = self.get_cities(prov["code"])
                cities.extend(prov_cities)
            except (requests.RequestException, KeyError):
                continue

        self._city_cache = cities
        return cities

    def find_stationid(self, city_name: str) -> Optional[dict]:
        """根据城市名查找站点信息

        支持模糊匹配：精确匹配优先，其次包含匹配
        """
        all_cities = self.get_all_cities()

        # 精确匹配
        for city in all_cities:
            if city.get("city") == city_name:
                return city

        # 包含匹配（处理"北京市"→"北京"等情况）
        # 只允许 city_label 是 city_name 的子串（用户输入比城市名长），
        # 不允许反向（用户输入"山"不应匹配"山东"）
        for city in all_cities:
            city_label = city.get("city", "")
            if city_label and city_label in city_name:
                return city

        return None

    def get_weather(self, stationid: str) -> dict:
        """根据 stationid 获取完整天气数据（实时 + 预报）"""
        data = self._get("/weather", params={"stationid": stationid})
        return data
