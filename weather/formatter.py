"""天气数据格式化输出"""

NA = "N/A"


def _clean(val, unit: str = "") -> str:
    """清洗 API 返回值：9999 / 9999.0 / None / 空字符串 → N/A"""
    if val is None or val == "":
        return NA
    try:
        if float(val) == 9999.0:
            return NA
    except (ValueError, TypeError):
        pass
    return f"{val}{unit}"


def format_weather(weather_data: dict) -> str:
    """将 nmc.cn API 返回的天气数据格式化为可读文本

    输出示例：
    ═══════════════════════════════════════
      北京 · 实时天气
    ═══════════════════════════════════════
      发布时间: 2026-08-04 23:10
      天气:     多云
      温度:     29.4℃  (体感 34.0℃)
      风向:     西南风 微风  1.3m/s
      湿度:     74%
      气压:     9999.0hPa
      降雨量:   0.0mm
      日出/日落: 05:15 / 19:24

    ── 未来 7 天预报 ──────────────────────
      08-04  夜间  雷阵雨  26℃    北风 微风
      08-05  白天  多云    33℃    南风 微风
      ...
    ═══════════════════════════════════════
    """
    real = weather_data.get("real", {})
    predict = weather_data.get("predict", {})
    station = real.get("station", {})
    city_name = station.get("city", "未知城市")

    # ── 实时天气 ──
    publish_time = _clean(real.get("publish_time"))
    w = real.get("weather", {})
    wind = real.get("wind", {})
    sun = real.get("sunriseSunset", {})

    temp = _clean(w.get("temperature"), "℃")
    feelst = _clean(w.get("feelst"), "℃")
    info = _clean(w.get("info"))
    humidity = _clean(w.get("humidity"), "%")
    pressure = _clean(w.get("airpressure"), "hPa")
    rain = _clean(w.get("rain"), "mm")
    wind_direct = _clean(wind.get("direct"))
    wind_power = _clean(wind.get("power"))
    wind_speed = _clean(wind.get("speed"), "m/s")

    sunrise = _extract_time(sun.get("sunrise", ""))
    sunset = _extract_time(sun.get("sunset", ""))

    wind_line = f"{wind_direct} {wind_power}"
    if wind_speed != NA:
        wind_line += f"  {wind_speed}"

    lines = []
    sep = "═" * 40
    lines.append(sep)
    lines.append(f"  {city_name} · 实时天气")
    lines.append(sep)
    lines.append(f"  发布时间: {publish_time}")
    lines.append(f"  天气:     {info}")
    lines.append(f"  温度:     {temp}  (体感 {feelst})")
    lines.append(f"  风向:     {wind_line}")
    lines.append(f"  湿度:     {humidity}")
    lines.append(f"  气压:     {pressure}")
    lines.append(f"  降雨量:   {rain}")
    lines.append(f"  日出/日落: {sunrise} / {sunset}")

    # ── 7天预报 ──
    detail = predict.get("detail", [])
    if detail:
        lines.append("")
        lines.append("── 未来 7 天预报 " + "─" * 24)
        for d in detail:
            date_str = _short_date(d.get("date", ""))
            day_weather = d.get("day", {})
            night_weather = d.get("night", {})
            day_info = day_weather.get("weather", {})
            night_info = night_weather.get("weather", {})
            day_wind = day_weather.get("wind", {})
            night_wind = night_weather.get("wind", {})

            # 白天
            day_w = day_info.get("info", "")
            day_t = day_info.get("temperature", "")
            day_d = day_wind.get("direct", "")
            day_p = day_wind.get("power", "")
            if day_w and day_w != "9999":
                lines.append(
                    f"  {date_str}  白天  {day_w}  {_clean(day_t, '℃')}  "
                    f"{_clean(day_d)} {_clean(day_p)}"
                )
            # 夜间
            night_w = night_info.get("info", "")
            night_t = night_info.get("temperature", "")
            night_d = night_wind.get("direct", "")
            night_p = night_wind.get("power", "")
            if night_w and night_w != "9999":
                lines.append(
                    f"  {date_str}  夜间  {night_w}  {_clean(night_t, '℃')}  "
                    f"{_clean(night_d)} {_clean(night_p)}"
                )

    lines.append(sep)
    return "\n".join(lines)


def _extract_time(datetime_str: str) -> str:
    """从 '2026-08-04 05:15' 提取 '05:15'"""
    if not datetime_str or datetime_str == "9999":
        return NA
    parts = str(datetime_str).split(" ")
    return parts[-1] if len(parts) > 1 else str(datetime_str)


def _short_date(date_str: str) -> str:
    """从 '2026-08-04' 提取 '08-04'"""
    if not date_str:
        return "??-??"
    parts = str(date_str).split("-")
    return "-".join(parts[1:]) if len(parts) >= 3 else str(date_str)


def format_forecast_by_date(weather_data: dict, city_name: str, dates: list[str]) -> str:
    """根据指定日期列表，从7天预报中筛选并格式化输出

    参数:
        weather_data: nmc.cn API 返回的天气数据
        city_name: 城市名称
        dates: 日期列表，格式 YYYY-MM-DD

    返回: 格式化文本，包含匹配到的预报和未匹配的提示
    """
    predict = weather_data.get("predict", {})
    detail = predict.get("detail", [])

    sep = "═" * 40
    lines = [sep, f"  {city_name} · 指定日期天气查询", sep]

    matched_dates = set()
    found_any = False

    for target_date in dates:
        found = False
        for d in detail:
            if d.get("date") == target_date:
                found = True
                matched_dates.add(target_date)
                found_any = True
                date_short = _short_date(target_date)
                lines.append("")
                lines.append(f"  📅 {date_short}")

                day_weather = d.get("day", {})
                night_weather = d.get("night", {})
                day_info = day_weather.get("weather", {})
                night_info = night_weather.get("weather", {})
                day_wind = day_weather.get("wind", {})
                night_wind = night_weather.get("wind", {})

                # 白天
                day_w = day_info.get("info", "")
                if day_w and day_w != "9999":
                    lines.append(
                        f"    白天  {_clean(day_w)}  {_clean(day_info.get('temperature'), '℃')}  "
                        f"{_clean(day_wind.get('direct'))} {_clean(day_wind.get('power'))}"
                    )
                # 夜间
                night_w = night_info.get("info", "")
                if night_w and night_w != "9999":
                    lines.append(
                        f"    夜间  {_clean(night_w)}  {_clean(night_info.get('temperature'), '℃')}  "
                        f"{_clean(night_wind.get('direct'))} {_clean(night_wind.get('power'))}"
                    )

                # 如果白天和夜间都为 9999
                if (not day_w or day_w == "9999") and (not night_w or night_w == "9999"):
                    lines.append(f"    该日期暂无天气数据")
                break

        if not found:
            lines.append("")
            lines.append(f"  📅 {_short_date(target_date)}")
            lines.append(f"    ❌ 该日期不在预报范围内（预报仅支持未来7天）")

    if not found_any and not matched_dates:
        lines.append("")
        lines.append(f"  ⚠️ 查询的日期均不在预报范围内")
        # 显示可查询的日期范围
        if detail:
            available = [_short_date(d.get("date", "")) for d in detail]
            lines.append(f"  可查询日期: {', '.join(available)}")

    lines.append(sep)
    return "\n".join(lines)
