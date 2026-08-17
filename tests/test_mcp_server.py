"""MCP Server 工具的单元测试（使用 mock，不依赖网络）"""

import unittest
from unittest.mock import patch

from weather.mcp_server import get_weather, get_forecast


# ── 测试用 mock 数据 ──
MOCK_RESULT = {
    "city_query": "北京",
    "station": {"city": "北京", "code": "Wqsps"},
    "data": {
        "real": {
            "station": {"city": "北京"},
            "publish_time": "2026-08-17 08:00",
            "weather": {
                "temperature": "29.4",
                "feelst": "34.0",
                "info": "多云",
                "humidity": "74",
                "airpressure": "1001.0",
                "rain": "0.0",
            },
            "wind": {"direct": "西南风", "power": "微风", "speed": "1.3"},
            "sunriseSunset": {"sunrise": "2026-08-17 05:15", "sunset": "2026-08-17 19:24"},
        },
        "predict": {
            "detail": [
                {
                    "date": "2026-08-17",
                    "day": {"weather": {"info": "多云", "temperature": "33"},
                            "wind": {"direct": "南风", "power": "微风"}},
                    "night": {"weather": {"info": "雷阵雨", "temperature": "26"},
                              "wind": {"direct": "北风", "power": "微风"}},
                },
                {
                    "date": "2026-08-18",
                    "day": {"weather": {"info": "晴", "temperature": "35"},
                            "wind": {"direct": "南风", "power": "微风"}},
                    "night": {"weather": {"info": "晴", "temperature": "27"},
                              "wind": {"direct": "南风", "power": "微风"}},
                },
            ]
        },
    },
}


class TestGetWeather(unittest.TestCase):
    """测试 get_weather MCP 工具"""

    @patch("weather.mcp_server.query_weather")
    def test_get_weather_success(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_weather("北京")
        self.assertIn("北京", result)
        self.assertIn("实时天气", result)
        self.assertIn("多云", result)
        self.assertIn("29.4℃", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_weather_city_not_found(self, mock_query):
        mock_query.side_effect = ValueError("未找到城市: 火星")
        result = get_weather("火星")
        self.assertIn("❌", result)
        self.assertIn("未找到城市", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_weather_api_error(self, mock_query):
        mock_query.side_effect = RuntimeError("接口异常")
        result = get_weather("北京")
        self.assertIn("❌", result)
        self.assertIn("获取天气数据失败", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_weather_includes_forecast(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_weather("北京")
        self.assertIn("未来 7 天预报", result)
        self.assertIn("08-17", result)


class TestGetForecast(unittest.TestCase):
    """测试 get_forecast MCP 工具"""

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_single_date(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "2026-08-17")
        self.assertIn("指定日期天气查询", result)
        self.assertIn("08-17", result)
        self.assertIn("多云", result)
        self.assertIn("雷阵雨", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_multi_dates(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "2026-08-17,2026-08-18")
        self.assertIn("08-17", result)
        self.assertIn("08-18", result)
        self.assertIn("晴", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_short_date_format(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "08-17")
        self.assertIn("08-17", result)
        self.assertIn("多云", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_date_not_in_range(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "2026-12-25")
        self.assertIn("不在预报范围内", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_invalid_date_format(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "abc")
        self.assertIn("没有有效的日期", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_mixed_valid_invalid(self, mock_query):
        mock_query.return_value = MOCK_RESULT
        result = get_forecast("北京", "2026-08-17,abc")
        self.assertIn("无法识别的日期格式", result)
        self.assertIn("08-17", result)

    @patch("weather.mcp_server.query_weather")
    def test_get_forecast_city_not_found(self, mock_query):
        mock_query.side_effect = ValueError("未找到城市: 火星")
        result = get_forecast("火星", "2026-08-17")
        self.assertIn("❌", result)
        self.assertIn("未找到城市", result)


if __name__ == "__main__":
    unittest.main()
