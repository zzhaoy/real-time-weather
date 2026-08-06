"""filter_forecast_json 的单元测试"""

import unittest

from main import filter_forecast_json


class TestFilterForecastJson(unittest.TestCase):
    """测试 filter_forecast_json 函数"""

    def setUp(self):
        self.sample_data = {
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
                            "weather": {"info": "9999", "temperature": "9999"},
                            "wind": {"direct": "9999", "power": "9999"},
                        },
                    },
                ],
            },
        }

    def test_single_date_found(self):
        """单日期匹配，返回正确天气数据"""
        result = filter_forecast_json(self.sample_data, ["2026-08-06"])
        self.assertEqual(len(result["dates"]), 1)
        entry = result["dates"][0]
        self.assertTrue(entry["found"])
        self.assertEqual(entry["day"]["weather"], "多云")
        self.assertEqual(entry["day"]["temperature"], "34")
        self.assertEqual(entry["night"]["temperature"], "28")

    def test_multiple_dates_found(self):
        """多日期匹配"""
        result = filter_forecast_json(self.sample_data, ["2026-08-06", "2026-08-07"])
        self.assertEqual(len(result["dates"]), 2)
        self.assertTrue(result["dates"][0]["found"])
        self.assertTrue(result["dates"][1]["found"])

    def test_date_not_found(self):
        """日期不在预报范围内"""
        result = filter_forecast_json(self.sample_data, ["2026-08-20"])
        entry = result["dates"][0]
        self.assertFalse(entry["found"])
        self.assertEqual(entry["date"], "2026-08-20")

    def test_partial_match(self):
        """部分日期匹配，部分不匹配"""
        result = filter_forecast_json(self.sample_data, ["2026-08-06", "2026-08-20"])
        self.assertTrue(result["dates"][0]["found"])
        self.assertFalse(result["dates"][1]["found"])

    def test_9999_cleaned_to_none(self):
        """9999 值应被清洗为 None"""
        result = filter_forecast_json(self.sample_data, ["2026-08-07"])
        entry = result["dates"][0]
        # 08-07 夜间全部为 9999
        self.assertIsNone(entry["night"]["weather"])
        self.assertIsNone(entry["night"]["temperature"])
        self.assertIsNone(entry["night"]["wind_direct"])
        self.assertIsNone(entry["night"]["wind_power"])

    def test_9999_float_string_cleaned(self):
        """字符串 '9999.0' 也应被清洗为 None"""
        data = {
            "predict": {
                "detail": [
                    {
                        "date": "2026-08-06",
                        "day": {
                            "weather": {"info": "9999.0", "temperature": "9999.0"},
                            "wind": {"direct": "9999.0", "power": "9999.0"},
                        },
                        "night": {
                            "weather": {"info": "晴", "temperature": "25"},
                            "wind": {"direct": "北风", "power": "微风"},
                        },
                    },
                ],
            },
        }
        result = filter_forecast_json(data, ["2026-08-06"])
        entry = result["dates"][0]
        self.assertIsNone(entry["day"]["weather"])
        self.assertIsNone(entry["day"]["temperature"])
        self.assertIsNone(entry["day"]["wind_direct"])
        self.assertIsNone(entry["day"]["wind_power"])

    def test_empty_forecast(self):
        """预报数据为空"""
        data = {"predict": {"detail": []}}
        result = filter_forecast_json(data, ["2026-08-06"])
        self.assertFalse(result["dates"][0]["found"])

    def test_no_predict_key(self):
        """数据中没有 predict 键"""
        data = {}
        result = filter_forecast_json(data, ["2026-08-06"])
        self.assertFalse(result["dates"][0]["found"])

    def test_day_and_night_structure(self):
        """验证返回的 day/night 结构完整性"""
        result = filter_forecast_json(self.sample_data, ["2026-08-06"])
        entry = result["dates"][0]
        self.assertIn("day", entry)
        self.assertIn("night", entry)
        self.assertIn("weather", entry["day"])
        self.assertIn("temperature", entry["day"])
        self.assertIn("wind_direct", entry["day"])
        self.assertIn("wind_power", entry["day"])
        self.assertIn("weather", entry["night"])
        self.assertIn("temperature", entry["night"])
        self.assertIn("wind_direct", entry["night"])
        self.assertIn("wind_power", entry["night"])


if __name__ == "__main__":
    unittest.main()
