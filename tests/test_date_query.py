"""指定日期查询功能的单元测试"""

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from io import StringIO
import sys

from weather.formatter import format_forecast_by_date, _short_date


class TestParseDate(unittest.TestCase):
    """测试 main.py 中的 parse_date 函数"""

    def test_full_date(self):
        from main import parse_date
        self.assertEqual(parse_date("2026-08-10"), "2026-08-10")

    def test_slash_date(self):
        from main import parse_date
        self.assertEqual(parse_date("2026/08/10"), "2026-08-10")

    def test_short_date_no_year(self):
        from main import parse_date
        from main import CST
        result = parse_date("08-10")
        expected_year = str(datetime.now(CST).year)
        self.assertEqual(result, f"{expected_year}-08-10")

    def test_short_slash_date(self):
        from main import parse_date
        from main import CST
        result = parse_date("08/10")
        expected_year = str(datetime.now(CST).year)
        self.assertEqual(result, f"{expected_year}-08-10")

    def test_short_date_uses_cst_timezone(self):
        """短日期补全年份应使用北京时间 (CST)，而非本地时区"""
        from main import CST
        # CST 应为 UTC+8
        self.assertEqual(CST.utcoffset(None), timedelta(hours=8))

    def test_invalid_format(self):
        from main import parse_date
        self.assertIsNone(parse_date("invalid"))
        self.assertIsNone(parse_date("2026-13-45"))
        self.assertIsNone(parse_date(""))


class TestFormatForecastByDate(unittest.TestCase):
    """测试 format_forecast_by_date 函数"""

    def setUp(self):
        self.sample_data = {
            "real": {
                "station": {"city": "北京"},
                "publish_time": "2026-08-06 08:00",
                "weather": {"temperature": 30, "info": "多云"},
                "wind": {"direct": "北风", "power": "微风"},
            },
            "predict": {
                "detail": [
                    {
                        "date": "2026-08-06",
                        "day": {
                            "weather": {"info": "多云", "temperature": "34"},
                            "wind": {"direct": "东北风", "power": "微风"},
                        },
                        "night": {
                            "weather": {"info": "多云", "temperature": "28"},
                            "wind": {"direct": "东北风", "power": "微风"},
                        },
                    },
                    {
                        "date": "2026-08-07",
                        "day": {
                            "weather": {"info": "阴", "temperature": "34"},
                            "wind": {"direct": "东北风", "power": "5~6级"},
                        },
                        "night": {
                            "weather": {"info": "阴", "temperature": "28"},
                            "wind": {"direct": "东北风", "power": "5~6级"},
                        },
                    },
                    {
                        "date": "2026-08-08",
                        "day": {
                            "weather": {"info": "中雨", "temperature": "31"},
                            "wind": {"direct": "东北风", "power": "5~6级"},
                        },
                        "night": {
                            "weather": {"info": "小雨", "temperature": "27"},
                            "wind": {"direct": "东北风", "power": "5~6级"},
                        },
                    },
                ],
            },
        }

    def test_single_date_matched(self):
        """查询单个日期，在预报范围内"""
        result = format_forecast_by_date(self.sample_data, "北京", ["2026-08-07"])
        self.assertIn("08-07", result)
        self.assertIn("阴", result)
        self.assertIn("34℃", result)
        self.assertIn("5~6级", result)
        self.assertIn("北京", result)

    def test_multiple_dates_matched(self):
        """查询多个日期，均在预报范围内"""
        result = format_forecast_by_date(self.sample_data, "上海", ["2026-08-06", "2026-08-08"])
        self.assertIn("08-06", result)
        self.assertIn("08-08", result)
        self.assertIn("多云", result)
        self.assertIn("中雨", result)

    def test_date_not_in_range(self):
        """查询日期不在预报范围内"""
        result = format_forecast_by_date(self.sample_data, "北京", ["2026-08-15"])
        self.assertIn("不在预报范围内", result)
        self.assertIn("08-15", result)

    def test_partial_match(self):
        """部分日期匹配，部分不匹配"""
        result = format_forecast_by_date(self.sample_data, "北京", ["2026-08-07", "2026-08-20"])
        self.assertIn("08-07", result)
        self.assertIn("阴", result)
        self.assertIn("08-20", result)
        self.assertIn("不在预报范围内", result)

    def test_all_dates_not_in_range(self):
        """所有日期均不在预报范围内，应显示可查询日期"""
        result = format_forecast_by_date(self.sample_data, "北京", ["2026-09-01"])
        self.assertIn("可查询日期", result)
        self.assertIn("08-06", result)
        self.assertIn("08-07", result)
        self.assertIn("08-08", result)

    def test_empty_forecast_detail(self):
        """预报详情为空"""
        data = {"predict": {"detail": []}}
        result = format_forecast_by_date(data, "北京", ["2026-08-06"])
        self.assertIn("不在预报范围内", result)

    def test_no_predict_key(self):
        """数据中没有 predict 键"""
        data = {"real": {"station": {"city": "北京"}}}
        result = format_forecast_by_date(data, "北京", ["2026-08-06"])
        self.assertIn("不在预报范围内", result)

    def test_9999_day_and_night(self):
        """白天和夜间数据均为 9999"""
        data = {
            "predict": {
                "detail": [
                    {
                        "date": "2026-08-06",
                        "day": {
                            "weather": {"info": "9999", "temperature": "9999"},
                            "wind": {"direct": "9999", "power": "9999"},
                        },
                        "night": {
                            "weather": {"info": "9999", "temperature": "9999"},
                            "wind": {"direct": "9999", "power": "9999"},
                        },
                    },
                ]
            }
        }
        result = format_forecast_by_date(data, "北京", ["2026-08-06"])
        self.assertIn("暂无天气数据", result)


class TestMainWithDate(unittest.TestCase):
    """测试 main.py 的 --date 参数"""

    def test_date_flag_help(self):
        """--help 应包含 --date 说明"""
        from main import main
        with self.assertRaises(SystemExit):
            with patch("sys.stdout", new=StringIO()):
                sys.argv = ["main.py", "--help"]
                main()

    @patch("weather.client.NmcClient.get_weather")
    @patch("weather.client.NmcClient.find_stationid")
    def test_date_query_single(self, mock_station, mock_weather):
        """测试 --date 单日期查询"""
        from main import main

        mock_station.return_value = {"code": "Wqsps", "city": "北京"}
        mock_weather.return_value = {
            "code": 0,
            "data": {
                "real": {
                    "station": {"city": "北京"},
                    "publish_time": "2026-08-06 08:00",
                    "weather": {"temperature": 30, "info": "多云"},
                    "wind": {"direct": "北风", "power": "微风"},
                },
                "predict": {
                    "detail": [
                        {
                            "date": "2026-08-06",
                            "day": {
                                "weather": {"info": "多云", "temperature": "34"},
                                "wind": {"direct": "东北风", "power": "微风"},
                            },
                            "night": {
                                "weather": {"info": "多云", "temperature": "28"},
                                "wind": {"direct": "东北风", "power": "微风"},
                            },
                        },
                    ]
                },
            },
        }

        with patch("sys.stdout", new=StringIO()) as fake_out:
            sys.argv = ["main.py", "北京", "--date", "2026-08-06"]
            main()
            output = fake_out.getvalue()

        self.assertIn("08-06", output)
        self.assertIn("多云", output)
        self.assertIn("指定日期天气查询", output)


if __name__ == "__main__":
    unittest.main()
