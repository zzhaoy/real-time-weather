# real-time-weather

实时天气查询工具，数据来源为中央气象台 (nmc.cn)。

## 功能

- 输入城市名称，查询实时天气
- 获取温度、湿度、风向、气压、降雨量等信息
- 查看未来 7 天天气预报
- 支持全国主要城市（含区县）

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python3 main.py 北京
python3 main.py 深圳
python3 main.py 成都市
```

## 示例输出

```
══════════════════════════════════════
  北京 · 实时天气
══════════════════════════════════════
  发布时间: 2026-08-04 23:15
  天气:     多云
  温度:     29.2℃  (体感 33.6℃)
  风向:     西南风 微风  1.5m/s
  湿度:     75.0%
  气压:     N/A
  降雨量:   0.0mm
  日出/日落: 05:15 / 19:24

── 未来 7 天预报 ────────────────────────
  08-04  夜间  雷阵雨  26℃  北风 微风
  08-05  白天  多云  35℃  南风 微风
  ...
══════════════════════════════════════
```

## 项目结构

```
real-time-weather/
├── main.py              # CLI 入口
├── requirements.txt     # 依赖
├── weather/
│   ├── __init__.py
│   ├── client.py        # nmc.cn API 客户端
│   └── formatter.py     # 天气数据格式化
└── tests/
    ├── __init__.py
    ├── test_client.py    # 客户端测试 (mock)
    └── test_formatter.py # 格式化测试
```

## 数据来源

- [中央气象台 nmc.cn](https://www.nmc.cn/publish/forecast.html)
- API: `/rest/province`, `/rest/province/{code}`, `/rest/weather?stationid={code}`

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```
