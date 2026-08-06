#!/usr/bin/env python3
"""实时天气查询工具

数据来源: 中央气象台 (nmc.cn)
用法:
    python3 main.py 北京
    python3 main.py --json 深圳
    python3 main.py 上海 --date 2026-08-10
    python3 main.py 上海 --date 2026-08-08,2026-08-10
"""

import argparse
import json
import sys
from datetime import datetime

from weather.formatter import format_weather, format_forecast_by_date, clean_value
from weather.service import query_weather


def parse_date(date_str: str) -> str | None:
    """解析日期字符串，返回 YYYY-MM-DD 格式，无效则返回 None

    支持: 2026-08-10, 08-10 (补全当前年份), 2026/08/10
    """
    date_str = date_str.strip()

    # 尝试多种日期格式
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d", "%m/%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if fmt in ("%m-%d", "%m/%d"):
                dt = dt.replace(year=datetime.now().year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="实时天气查询工具 (数据来源: 中央气象台 nmc.cn)",
    )
    parser.add_argument("city", help="城市名称，如：北京、上海")
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出机器可读 JSON，便于 trip-planner 等上层应用调用",
    )
    parser.add_argument(
        "--date", "-d",
        help="查询指定日期的天气，支持逗号分隔多日期，如：2026-08-10 或 08-10,08-11",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        result = query_weather(args.city)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print("提示: 请确认城市名称是否正确，目前支持全国主要城市", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"获取天气数据失败: {exc}", file=sys.stderr)
        sys.exit(1)

    data = result["data"]
    matched_city = result["station"].get("city", args.city)

    # 按日期查询
    if args.date:
        raw_dates = [d.strip() for d in args.date.split(",") if d.strip()]
        dates = []
        invalid_dates = []
        for raw in raw_dates:
            parsed = parse_date(raw)
            if parsed:
                dates.append(parsed)
            else:
                invalid_dates.append(raw)

        if invalid_dates:
            print(f"⚠️ 无法识别的日期格式: {', '.join(invalid_dates)}", file=sys.stderr)
            print("支持格式: YYYY-MM-DD (如 2026-08-10) 或 MM-DD (如 08-10)", file=sys.stderr)

        if not dates:
            print("❌ 没有有效的日期，无法查询", file=sys.stderr)
            sys.exit(1)

        if args.json:
            forecast = filter_forecast_json(data, dates)
            print(json.dumps(forecast, ensure_ascii=False, indent=2))
        else:
            print(format_forecast_by_date(data, matched_city, dates))
        return

    # 默认输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_weather(data))


def filter_forecast_json(data: dict, dates: list[str]) -> dict:
    """从天气数据中按日期筛选预报，返回 JSON 友好结构"""
    predict = data.get("predict", {})
    detail = predict.get("detail", [])

    results = []
    for target_date in dates:
        entry = {"date": target_date, "found": False}
        for d in detail:
            if d.get("date") == target_date:
                entry["found"] = True
                day_w = d.get("day", {}).get("weather", {})
                night_w = d.get("night", {}).get("weather", {})
                day_wind = d.get("day", {}).get("wind", {})
                night_wind = d.get("night", {}).get("wind", {})
                entry["day"] = {
                    "weather": clean_value(day_w.get("info")),
                    "temperature": clean_value(day_w.get("temperature")),
                    "wind_direct": clean_value(day_wind.get("direct")),
                    "wind_power": clean_value(day_wind.get("power")),
                }
                entry["night"] = {
                    "weather": clean_value(night_w.get("info")),
                    "temperature": clean_value(night_w.get("temperature")),
                    "wind_direct": clean_value(night_wind.get("direct")),
                    "wind_power": clean_value(night_wind.get("power")),
                }
                break
        results.append(entry)

    return {"dates": results}


if __name__ == "__main__":
    main()
