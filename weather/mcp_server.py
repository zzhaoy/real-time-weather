"""real-time-weather MCP Server

将中央气象台天气查询能力暴露为 MCP 工具，供 MCP Client（如 Codex、Claude）调用。

工具:
    - get_weather: 查询城市实时天气 + 未来 7 天预报
    - get_forecast: 按指定日期查询天气预报

传输方式:
    - stdio (默认): 本地进程通信，适合 CLI / IDE 集成
    - streamable-http: HTTP 单端点传输，适合远程部署

启动:
    # stdio 模式（默认）
    python -m weather.mcp_server

    # Streamable HTTP 模式
    python -m weather.mcp_server --transport streamable-http
    python -m weather.mcp_server -t streamable-http --host 0.0.0.0 --port 9000
"""

from __future__ import annotations

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from weather.service import query_weather
from weather.formatter import format_weather, format_forecast_by_date


mcp = FastMCP("real-time-weather")


@mcp.tool()
def get_weather(city: str) -> str:
    """查询城市实时天气和未来7天预报

    Args:
        city: 城市名称，如 "北京"、"上海"、"深圳市"

    Returns:
        格式化的天气信息文本，包含实时天气和7天预报
    """
    try:
        result = query_weather(city)
    except ValueError as exc:
        return f"❌ {exc}"
    except Exception as exc:
        return f"❌ 获取天气数据失败: {exc}"

    return format_weather(result["data"])


@mcp.tool()
def get_forecast(city: str, dates: str) -> str:
    """查询城市指定日期的天气预报

    Args:
        city: 城市名称，如 "北京"、"上海"
        dates: 日期字符串，支持逗号分隔多日期，格式 YYYY-MM-DD 或 MM-DD，如 "2026-08-10" 或 "08-10,08-11"

    Returns:
        格式化的指定日期天气预报文本
    """
    from main import parse_date

    try:
        result = query_weather(city)
    except ValueError as exc:
        return f"❌ {exc}"
    except Exception as exc:
        return f"❌ 获取天气数据失败: {exc}"

    data = result["data"]
    matched_city = result["station"].get("city", city)

    raw_dates = [d.strip() for d in dates.split(",") if d.strip()]
    parsed_dates: list[str] = []
    invalid_dates: list[str] = []

    for raw in raw_dates:
        parsed = parse_date(raw)
        if parsed:
            parsed_dates.append(parsed)
        else:
            invalid_dates.append(raw)

    if invalid_dates:
        invalid_note = f"⚠️ 无法识别的日期格式: {', '.join(invalid_dates)}\n\n"
    else:
        invalid_note = ""

    if not parsed_dates:
        return f"❌ 没有有效的日期，无法查询。支持格式: YYYY-MM-DD (如 2026-08-10) 或 MM-DD (如 08-10)"

    forecast_text = format_forecast_by_date(data, matched_city, parsed_dates)
    return invalid_note + forecast_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="real-time-weather MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  # stdio 模式（默认，本地 IDE 集成）
  python -m weather.mcp_server

  # Streamable HTTP 模式
  python -m weather.mcp_server -t streamable-http
  python -m weather.mcp_server -t streamable-http --host 0.0.0.0 --port 9000
""",
    )
    parser.add_argument(
        "-t", "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="传输方式 (默认: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 监听地址，仅 streamable-http 模式生效 (默认: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP 监听端口，仅 streamable-http 模式生效 (默认: 8000)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.transport == "streamable-http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        print(f"🌐 Streamable HTTP 模式: http://{args.host}:{args.port}/mcp", file=sys.stderr)
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
