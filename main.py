#!/usr/bin/env python3
"""实时天气查询工具

数据来源: 中央气象台 (nmc.cn)
用法:
    python3 main.py 北京
    python3 main.py --json 深圳
"""

import argparse
import json
import sys

from weather.formatter import format_weather
from weather.service import query_weather


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询中央气象台实时天气")
    parser.add_argument("city", help="城市名称，例如：北京、深圳、成都市")
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出机器可读 JSON，便于 trip-planner 等上层应用调用",
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

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(format_weather(result["data"]))


if __name__ == "__main__":
    main()
