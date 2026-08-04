"""service 模块的单元测试（使用 fake client，不依赖网络）"""

import unittest

from weather.service import query_weather


class FakeClient:
    def __init__(self, station=None, weather=None):
        self.station = station
        self.weather = weather or {"code": 0, "data": {"real": {"station": {"city": "北京"}}}}

    def find_stationid(self, city_name):
        return self.station

    def get_weather(self, stationid):
        return self.weather


class TestQueryWeather(unittest.TestCase):
    def test_query_weather_success(self):
        station = {"code": "Wqsps", "city": "北京", "province": "北京市"}
        result = query_weather(" 北京 ", FakeClient(station=station))

        self.assertEqual(result["city_query"], "北京")
        self.assertEqual(result["station"], station)
        self.assertIn("real", result["data"])

    def test_empty_city_rejected(self):
        with self.assertRaisesRegex(ValueError, "城市名称不能为空"):
            query_weather("  ", FakeClient())

    def test_city_not_found(self):
        with self.assertRaisesRegex(ValueError, "未找到城市"):
            query_weather("不存在的城市", FakeClient(station=None))

    def test_api_error(self):
        station = {"code": "Wqsps", "city": "北京"}
        weather = {"code": 1, "msg": "接口限流"}

        with self.assertRaisesRegex(RuntimeError, "接口限流"):
            query_weather("北京", FakeClient(station=station, weather=weather))

    def test_missing_real_data(self):
        station = {"code": "Wqsps", "city": "北京"}
        weather = {"code": 0, "data": {}}

        with self.assertRaisesRegex(RuntimeError, "暂无 北京 的天气数据"):
            query_weather("北京", FakeClient(station=station, weather=weather))


if __name__ == "__main__":
    unittest.main()
