"""formatter 模块的单元测试"""

import unittest

from weather.formatter import (
    format_weather,
    _clean,
    _extract_time,
    _short_date,
)


class TestClean(unittest.TestCase):
    """测试 _clean 函数"""

    def test_normal_value(self):
        self.assertEqual(_clean(29.4, "℃"), "29.4℃")

    def test_none(self):
        self.assertEqual(_clean(None), "N/A")

    def test_empty_string(self):
        self.assertEqual(_clean(""), "N/A")

    def test_9999_string(self):
        self.assertEqual(_clean("9999"), "N/A")

    def test_9999_int(self):
        self.assertEqual(_clean(9999), "N/A")

    def test_9999_float(self):
        self.assertEqual(_clean(9999.0, "hPa"), "N/A")

    def test_with_unit(self):
        self.assertEqual(_clean(74, "%"), "74%")

    def test_dash_value(self):
        """'-' 是有效的天气描述，不应被过滤"""

    def test_9999_string_float(self):
        """字符串 "9999.0" 应被识别为无效值"""
        self.assertEqual(_clean("9999.0"), "N/A")
        self.assertEqual(_clean("9999.0", "hPa"), "N/A")

    def test_9999_string_float_with_decimal(self):
        """字符串 "9999.00" 也应被识别为无效值"""
        self.assertEqual(_clean("9999.00"), "N/A")
        self.assertEqual(_clean("-"), "-")


class TestExtractTime(unittest.TestCase):
    """测试 _extract_time 函数"""

    def test_normal_datetime(self):
        self.assertEqual(_extract_time("2026-08-04 05:15"), "05:15")

    def test_9999(self):
        self.assertEqual(_extract_time("9999"), "N/A")

    def test_empty(self):
        self.assertEqual(_extract_time(""), "N/A")

    def test_time_only(self):
        self.assertEqual(_extract_time("19:24"), "19:24")


class TestShortDate(unittest.TestCase):
    """测试 _short_date 函数"""

    def test_normal_date(self):
        self.assertEqual(_short_date("2026-08-04"), "08-04")

    def test_empty(self):
        self.assertEqual(_short_date(""), "??-??")

    def test_partial_date(self):
        self.assertEqual(_short_date("08-04"), "08-04")


class TestFormatWeather(unittest.TestCase):
    """测试 format_weather 函数"""

    def setUp(self):
        self.sample_data = {
            "real": {
                "station": {
                    "city": "北京",
                    "code": "Wqsps",
                    "province": "北京市",
                    "url": "/publish/forecast/ABJ/beijing.html",
                },
                "publish_time": "2026-08-04 23:10",
                "weather": {
                    "temperature": 29.4,
                    "temperatureDiff": 4.0,
                    "airpressure": 9999.0,
                    "humidity": 74.0,
                    "rain": 0.0,
                    "info": "多云",
                    "img": "1",
                    "feelst": 34.0,
                },
                "wind": {
                    "direct": "西南风",
                    "degree": 200.0,
                    "power": "微风",
                    "speed": 1.3,
                },
                "warn": {},
                "sunriseSunset": {
                    "sunrise": "2026-08-04 05:15",
                    "sunset": "2026-08-04 19:24",
                },
            },
            "predict": {
                "station": {
                    "city": "北京",
                    "code": "Wqsps",
                },
                "publish_time": "2026-08-04 20:00",
                "detail": [
                    {
                        "date": "2026-08-04",
                        "day": {
                            "weather": {"info": "9999", "img": "9999",
                                        "temperature": "9999"},
                            "wind": {"direct": "9999", "power": "9999"},
                        },
                        "night": {
                            "weather": {"info": "雷阵雨", "img": "4",
                                        "temperature": "26"},
                            "wind": {"direct": "北风", "power": "微风"},
                        },
                    },
                    {
                        "date": "2026-08-05",
                        "day": {
                            "weather": {"info": "多云", "img": "1",
                                        "temperature": "35"},
                            "wind": {"direct": "南风", "power": "微风"},
                        },
                        "night": {
                            "weather": {"info": "多云", "img": "1",
                                        "temperature": "26"},
                            "wind": {"direct": "南风", "power": "微风"},
                        },
                    },
                ],
            },
        }

    def test_output_contains_city_name(self):
        result = format_weather(self.sample_data)
        self.assertIn("北京", result)

    def test_output_contains_temperature(self):
        result = format_weather(self.sample_data)
        self.assertIn("29.4℃", result)
        self.assertIn("体感 34.0℃", result)

    def test_output_contains_weather_info(self):
        result = format_weather(self.sample_data)
        self.assertIn("多云", result)

    def test_output_contains_wind(self):
        result = format_weather(self.sample_data)
        self.assertIn("西南风", result)
        self.assertIn("1.3m/s", result)

    def test_output_contains_humidity(self):
        result = format_weather(self.sample_data)
        self.assertIn("74.0%", result)

    def test_9999_pressure_cleaned(self):
        result = format_weather(self.sample_data)
        self.assertNotIn("9999", result)

    def test_output_contains_forecast(self):
        result = format_weather(self.sample_data)
        self.assertIn("未来 7 天预报", result)
        self.assertIn("雷阵雨", result)
        self.assertIn("08-05", result)

    def test_9999_day_forecast_skipped(self):
        """白天气息为 9999 时应跳过，只显示夜间"""
        result = format_weather(self.sample_data)
        # 08-04 白天为 9999，应只出现夜间行
        # 08-04 白天为 9999，应只出现夜间行
        # 只检查预报区域的行
        forecast_lines = [
            line for line in result.split("\n")
            if line.strip().startswith("08-04") and ("白天" in line or "夜间" in line)
        ]
        self.assertEqual(len(forecast_lines), 1)
        self.assertIn("夜间", forecast_lines[0])

    def test_output_contains_sunrise_sunset(self):
        result = format_weather(self.sample_data)
        self.assertIn("05:15", result)
        self.assertIn("19:24", result)

    def test_empty_data(self):
        """空数据不应抛异常"""
        result = format_weather({})
        self.assertIn("未知城市", result)

    def test_minimal_data(self):
        """最小数据集"""
        minimal = {
            "real": {
                "station": {"city": "测试城市"},
                "publish_time": "2026-08-04 12:00",
                "weather": {"temperature": 20, "info": "晴"},
                "wind": {"direct": "北风", "power": "微风"},
            }
        }
        result = format_weather(minimal)
        self.assertIn("测试城市", result)
        self.assertIn("20℃", result)
        self.assertIn("晴", result)


if __name__ == "__main__":
    unittest.main()
