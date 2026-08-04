#!/usr/bin/env python3
"""实时天气查询工具

数据来源: 中央气象台 (nmc.cn)
用法:
    python3 main.py 北京
    python3 main.py 深圳
    python3 main.py 上海
"""

import sys

from weather.client import NmcClient
from weather.formatter import format_weather


def main():
    if len(sys.argv) < 2:
        print("用法: python3 main.py <城市名称>")
        print("示例: python3 main.py 北京")
        sys.exit(1)

    city_name = sys.argv[1].strip()
    client = NmcClient()

    # 1. 查找城市 stationid
    station_info = client.find_stationid(city_name)
    if not station_info:
        print(f"未找到城市: {city_name}")
        print("提示: 请确认城市名称是否正确，目前支持全国主要城市")
        sys.exit(1)

    stationid = station_info["code"]
    matched_city = station_info.get("city", city_name)

    # 2. 获取天气
    try:
        weather_data = client.get_weather(stationid)
    except Exception as e:
        print(f"获取天气数据失败: {e}")
        sys.exit(1)

    # 3. 格式化输出
    if weather_data.get("code") != 0:
        print(f"接口返回错误: {weather_data.get('msg', '未知错误')}")
        sys.exit(1)

    data = weather_data.get("data", {})
    if not data or not data.get("real"):
        print(f"暂无 {matched_city} 的天气数据")
        sys.exit(1)

    print(format_weather(data))


if __name__ == "__main__":
    main()
