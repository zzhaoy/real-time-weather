# real-time-weather

实时天气查询工具，数据来源为中央气象台 (nmc.cn)。可作为 CLI 使用，也可输出 JSON 供 trip-planner 等上层应用调用。

## 功能

- 输入城市名称，查询实时天气
- 获取温度、湿度、风向、气压、降雨量等信息
- 查看未来 7 天天气预报
- **指定日期查询天气**，支持单日期或多日期逗号分隔
- 支持全国主要城市（含区县）
- 支持机器可读 JSON 输出，便于服务间集成

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 查询实时天气

```bash
python3 main.py 北京
python3 main.py 深圳
python3 main.py 成都市
```

### 指定日期查询

```bash
# 单日期
python3 main.py 上海 --date 2026-08-10

# 多日期（逗号分隔）
python3 main.py 上海 --date 2026-08-08,2026-08-10

# 短日期格式（自动补全当前年份）
python3 main.py 北京 --date 08-10
python3 main.py 北京 --date 08-08,08/10
```

支持的日期格式：

| 格式 | 示例 |
|------|------|
| YYYY-MM-DD | 2026-08-10 |
| YYYY/MM/DD | 2026/08/10 |
| MM-DD | 08-10 |
| MM/DD | 08/10 |

> ⚠️ 日期超出未来 7 天预报范围时会提示可查询的日期。

### JSON 输出模式

如需给 trip-planner 等上层应用调用，建议使用 JSON 模式：

```bash
python3 main.py --json 北京
python3 main.py --json 上海 --date 2026-08-10
```

### Python 代码调用

```python
from weather.service import query_weather

weather = query_weather("北京")
print(weather["data"]["real"]["weather"]["temperature"])
```

## 示例输出

### 实时天气

```text
════════════════════════════════════════
  北京 · 实时天气
════════════════════════════════════════
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
════════════════════════════════════════
```

### 指定日期查询

```text
════════════════════════════════════════
  上海 · 指定日期天气查询
════════════════════════════════════════

  📅 08-08
    白天  中雨  31℃  东北风 5~6级
    夜间  小雨  27℃  东北风 5~6级

  📅 08-11
    白天  大雨  31℃  东南风 微风
    夜间  中雨  26℃  东南风 微风

  📅 08-20
    ❌ 该日期不在预报范围内（预报仅支持未来7天）
════════════════════════════════════════
```

## 项目结构

```text
real-time-weather/
├── main.py              # CLI 入口
├── requirements.txt     # 依赖
├── weather/
│   ├── __init__.py
│   ├── client.py        # nmc.cn API 客户端
│   ├── formatter.py     # 天气数据格式化
│   └── service.py       # 上层应用可调用的查询服务
└── tests/
    ├── __init__.py
    ├── test_client.py     # 客户端测试 (mock)
    ├── test_formatter.py  # 格式化测试
    ├── test_service.py    # 服务层测试
    └── test_date_query.py # 指定日期查询测试
```

## 数据来源

- [中央气象台 nmc.cn](https://www.nmc.cn/publish/forecast.html)
- API: `/rest/province`, `/rest/province/{code}`, `/rest/weather?stationid={code}`

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```
