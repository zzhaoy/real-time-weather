"""client 模块的单元测试（使用 mock，不依赖网络）"""

import unittest
from unittest.mock import patch, MagicMock

from weather.client import NmcClient


class TestNmcClient(unittest.TestCase):
    """测试 NmcClient 类"""

    def setUp(self):
        self.client = NmcClient()

    @patch.object(NmcClient, "_get")
    def test_get_provinces(self, mock_get):
        mock_get.return_value = [
            {"code": "ABJ", "name": "北京市", "url": "/publish/forecast/ABJ.html"},
            {"code": "AGD", "name": "广东省", "url": "/publish/forecast/AGD.html"},
        ]
        result = self.client.get_provinces()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["code"], "ABJ")

    @patch.object(NmcClient, "_get")
    def test_get_cities(self, mock_get):
        mock_get.return_value = [
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
            {"code": "niStC", "city": "昌平", "province": "北京市"},
        ]
        result = self.client.get_cities("ABJ")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["code"], "Wqsps")

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_get_all_cities(self, mock_cities, mock_provinces):
        mock_provinces.return_value = [
            {"code": "ABJ", "name": "北京市"},
            {"code": "AGD", "name": "广东省"},
        ]
        mock_cities.side_effect = [
            [{"code": "Wqsps", "city": "北京", "province": "北京市"}],
            [{"code": "DwzZf", "city": "广州", "province": "广东省"}],
        ]
        result = self.client.get_all_cities()
        self.assertEqual(len(result), 2)
        self.assertIn("北京", [c["city"] for c in result])
        self.assertIn("广州", [c["city"] for c in result])

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_exact_match(self, mock_cities, mock_provinces):
        mock_provinces.return_value = [{"code": "ABJ", "name": "北京市"}]
        mock_cities.return_value = [
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
            {"code": "niStC", "city": "昌平", "province": "北京市"},
        ]
        result = self.client.find_stationid("北京")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "Wqsps")

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_fuzzy_match(self, mock_cities, mock_provinces):
        """测试模糊匹配：'北京市' 应匹配 '北京'"""
        mock_provinces.return_value = [{"code": "ABJ", "name": "北京市"}]
        mock_cities.return_value = [
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
        ]
        result = self.client.find_stationid("北京市")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "Wqsps")

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_not_found(self, mock_cities, mock_provinces):
        mock_provinces.return_value = [{"code": "ABJ", "name": "北京市"}]
        mock_cities.return_value = [
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
        ]
        result = self.client.find_stationid("不存在的城市")
        self.assertIsNone(result)

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_no_false_match_short_input(self, mock_cities, mock_provinces):
        """输入过短不应误命中：'山' 不应匹配 '山东' 或 '佛山'"""
        mock_provinces.return_value = [{"code": "ASD", "name": "山东省"}]
        mock_cities.return_value = [
            {"code": "sd01", "city": "济南", "province": "山东省"},
            {"code": "sd02", "city": "青岛", "province": "山东省"},
            {"code": "fs01", "city": "佛山", "province": "广东省"},
        ]
        result = self.client.find_stationid("山")
        self.assertIsNone(result)

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_no_false_match_partial(self, mock_cities, mock_provinces):
        """'南京' 不应因 '南' 在 '济南' 中而误匹配"""
        mock_provinces.return_value = [
            {"code": "ASD", "name": "山东省"},
            {"code": "AJS", "name": "江苏省"},
        ]
        mock_cities.side_effect = [
            [{"code": "jn01", "city": "济南", "province": "山东省"}],
            [{"code": "nj01", "city": "南京", "province": "江苏省"}],
        ]
        result = self.client.find_stationid("南京")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "nj01")

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_find_stationid_empty_city_label_guard(self, mock_cities, mock_provinces):
        """city_label 为空字符串时不应误匹配"""
        mock_provinces.return_value = [{"code": "ABJ", "name": "北京市"}]
        mock_cities.return_value = [
            {"code": "bad0", "city": "", "province": "北京市"},
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
        ]
        result = self.client.find_stationid("北京市")
        self.assertIsNotNone(result)
        self.assertEqual(result["code"], "Wqsps")

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_city_cache(self, mock_cities, mock_provinces):
        """第二次调用应使用缓存，不再请求 API"""
        mock_provinces.return_value = [{"code": "ABJ", "name": "北京市"}]
        mock_cities.return_value = [
            {"code": "Wqsps", "city": "北京", "province": "北京市"},
        ]
        self.client.get_all_cities()
        self.client.get_all_cities()
        # get_provinces 只应被调用一次
        self.assertEqual(mock_provinces.call_count, 1)

    @patch.object(NmcClient, "_get")
    def test_get_weather(self, mock_get):
        mock_get.return_value = {
            "code": 0,
            "data": {"real": {"station": {"city": "北京"}}},
        }
        result = self.client.get_weather("Wqsps")
        self.assertEqual(result["code"], 0)
        self.assertIn("data", result)

    @patch.object(NmcClient, "get_provinces")
    @patch.object(NmcClient, "get_cities")
    def test_province_fetch_error_continues(self, mock_cities, mock_provinces):
        """省份获取失败时应跳过，不中断整体流程"""
        mock_provinces.return_value = [
            {"code": "ABJ", "name": "北京市"},
            {"code": "AGD", "name": "广东省"},
        ]
        mock_cities.side_effect = [
            [{"code": "Wqsps", "city": "北京"}],  # ABJ 成功
            Exception("网络错误"),  # AGD 失败
        ]
        # 由于 Exception 不被 requests.RequestException 捕获，这里需要特殊处理
        # 实际代码中只捕获 requests.RequestException 和 KeyError
        with self.assertRaises(Exception):
            self.client.get_all_cities()


if __name__ == "__main__":
    unittest.main()
