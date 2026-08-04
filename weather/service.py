"""面向上层应用调用的天气查询服务。"""

from __future__ import annotations

from typing import Any

from weather.client import NmcClient


def query_weather(city_name: str, client: NmcClient | None = None) -> dict[str, Any]:
    """查询城市天气并返回稳定的机器可读结构。"""
    normalized_city = city_name.strip()
    if not normalized_city:
        raise ValueError("城市名称不能为空")

    weather_client = client or NmcClient()
    station_info = weather_client.find_stationid(normalized_city)
    if not station_info:
        raise ValueError(f"未找到城市: {normalized_city}")

    stationid = station_info["code"]
    response = weather_client.get_weather(stationid)
    if response.get("code") != 0:
        raise RuntimeError(response.get("msg", "天气接口返回错误"))

    data = response.get("data", {})
    if not data or not data.get("real"):
        matched_city = station_info.get("city", normalized_city)
        raise RuntimeError(f"暂无 {matched_city} 的天气数据")

    return {
        "city_query": normalized_city,
        "station": station_info,
        "data": data,
    }
