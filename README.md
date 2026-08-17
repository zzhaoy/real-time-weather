# real-time-weather

实时天气查询工具，数据来源为中央气象台 (nmc.cn)。可作为 CLI 使用，也可输出 JSON 供 trip-planner 等上层应用调用，还支持作为 **MCP Server** 接入 AI 工具（如 Codex、Claude Desktop）。

## 功能

- 输入城市名称，查询实时天气
- 获取温度、湿度、风向、气压、降雨量等信息
- 查看未来 7 天天气预报
- **指定日期查询天气**，支持单日期或多日期逗号分隔
- 支持全国主要城市（含区县）
- 支持机器可读 JSON 输出，便于服务间集成
- **MCP Server 模式**，作为工具接入 AI 客户端

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

## MCP Server 模式

本项目可作为 MCP (Model Context Protocol) Server 运行，将天气查询能力暴露为 AI 工具。支持两种传输方式：

- **stdio**（默认）：本地进程通信，适合 CLI / IDE 集成
- **streamable-http**：HTTP 单端点传输，适合远程部署

### 启动

```bash
# stdio 模式（默认，本地 IDE 集成）
python -m weather.mcp_server

# Streamable HTTP 模式（远程部署）
python -m weather.mcp_server -t streamable-http

# 自定义地址和端口
python -m weather.mcp_server -t streamable-http --host 0.0.0.0 --port 9000
```

### 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--transport` | `-t` | `stdio` | 传输方式：`stdio` 或 `streamable-http` |
| `--host` | — | `127.0.0.1` | HTTP 监听地址（仅 streamable-http 生效） |
| `--port` | — | `8000` | HTTP 监听端口（仅 streamable-http 生效） |

### 暴露的工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_weather` | `city: str` | 查询城市实时天气 + 未来 7 天预报 |
| `get_forecast` | `city: str`, `dates: str` | 按指定日期查询天气预报，支持逗号分隔多日期 |

### Codex 配置（stdio 模式）

在 `~/.codex/config.toml` 中添加：

```toml
[mcp_servers.real-time-weather]
command = "python"
args = ["-m", "weather.mcp_server"]
cwd = "/path/to/real-time-weather"
```

### Claude Desktop 配置（stdio 模式）

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "real-time-weather": {
      "command": "python",
      "args": ["-m", "weather.mcp_server"],
      "cwd": "/path/to/real-time-weather"
    }
  }
}
```

### Streamable HTTP 远程部署

启动服务后，客户端通过 `http://<host>:<port>/mcp` 端点连接。单端点设计，支持无状态部署和负载均衡。

#### 启动服务

```bash
python -m weather.mcp_server -t streamable-http --host 0.0.0.0 --port 8000
```

#### Codex 配置（streamable-http 模式）

在 `~/.codex/config.toml` 中添加：

```toml
[mcp_servers.real-time-weather]
url = "http://localhost:8000/mcp"
```

> 远程部署时将 `localhost:8000` 替换为实际地址和端口。

#### 客户端调用流程

streamable-http 协议是有状态的，必须按 **初始化 → 通知就绪 → 调用工具** 三步进行，每一步都需要携带前一步获取的 `Mcp-Session-Id`：

```bash
# ① 初始化握手，获取 session-id
SESSION_ID=$(curl -s -D - -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | grep -i 'mcp-session-id' | tr -d '\r\n' | awk '{print $2}')

echo "Session: $SESSION_ID"

# ② 发送 initialized 通知（携带 session-id）
curl -s -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# ③ 调用工具（携带 session-id）
curl -s -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather","arguments":{"city":"上海"}}}'
```

#### 请求头要求

| Header | 必填 | 说明 |
|--------|------|------|
| `Content-Type: application/json` | ✅ | JSON-RPC 请求体格式 |
| `Accept: application/json, text/event-stream` | ✅ | 必须同时接受两种类型，否则返回 `406 Not Acceptable` |
| `Mcp-Session-Id: <id>` | ✅（初始化之后） | 从 initialize 响应头获取，后续请求必须携带，否则返回 `400 Bad Request` |

#### 常见报错

| 报错 | 原因 | 解决 |
|------|------|------|
| `404 Not Found` | 请求路径不是 `/mcp`（如访问了 `/`） | 确保请求 `http://host:port/mcp` |
| `406 Not Acceptable` | 缺少 `Accept` header | 添加 `-H 'Accept: application/json, text/event-stream'` |
| `400 Bad Request: Missing session ID` | 缺少 `Mcp-Session-Id` header | 先执行 initialize 获取 session-id，后续请求携带该 header |

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
│   ├── service.py       # 上层应用可调用的查询服务
│   └── mcp_server.py    # MCP Server（工具暴露层）
└── tests/
    ├── __init__.py
    ├── test_client.py     # 客户端测试 (mock)
    ├── test_formatter.py  # 格式化测试
    ├── test_service.py    # 服务层测试
    ├── test_date_query.py # 指定日期查询测试
    ├── test_json_output.py # JSON 输出测试
    └── test_mcp_server.py  # MCP Server 工具测试
```

## 数据来源

- [中央气象台 nmc.cn](https://www.nmc.cn/publish/forecast.html)
- API: `/rest/province`, `/rest/province/{code}`, `/rest/weather?stationid={code}`

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```
