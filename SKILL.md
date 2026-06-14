---
name: stock-watcher
description: Manage and monitor a personal stock watchlist with real-time data from East Money (东方财富). Supports adding/removing stocks, price/percentage alerts, and automatic limit-up/limit-down detection with WeChat notifications. Use when tracking stocks, setting price alerts, or checking market performance.
---

# Stock Watcher Skill

个人自选股监控系统，使用**东方财富 API** 获取实时行情数据。支持自定义价格/涨跌幅预警、自动涨跌停检测，以及微信推送通知。

## 功能

### 自选股管理

| 操作 | 命令 |
|------|------|
| 添加股票 | `python3 manage_stocks.py add 603916` |
| 删除股票 | `python3 manage_stocks.py remove 603916` |
| 查看列表 | `python3 manage_stocks.py list` |
| 清空列表 | `python3 manage_stocks.py clear` |

### 行情查看

```bash
python3 summarize_performance.py
```

显示每只股票的：最新价、涨跌幅、今开/最高/最低/昨收、成交量、成交额、换手率、市盈率、市净率、总市值、流通市值。

### 价格/涨跌幅预警

自定义阈值触发提醒：

```bash
# 设置预警（价格超过15元或涨幅超过5%时提醒，触发后自动删除）
python3 manage_alerts.py add 603916 --above 15 --pct-above 5 --once

# 查看所有预警
python3 manage_alerts.py list

# 移除指定预警条件
python3 manage_alerts.py remove 603916 --above

# 清空所有预警
python3 manage_alerts.py clear
```

支持的预警条件：
- `--above <price>` — 价格超过触发
- `--below <price>` — 价格跌破触发
- `--pct-above <pct>` — 涨幅超过触发（如 5 表示 +5%）
- `--pct-below <pct>` — 跌幅超过触发（如 -3 表示 -3%）
- `--once` — 触发后自动删除该规则

### 自动涨跌停检测

无需配置，自动检查**所有自选股**。支持：
- **主板**（6/0/3开头）：±10%
- **科创板**（688开头）：±20%
- **创业板**（00开头）：±20%

检测到涨跌停自动触发预警并推送通知。

## 数据存储

| 文件 | 路径 |
|------|------|
| 自选股列表 | `~/.clawdbot/stock_watcher/watchlist.txt` |
| 预警规则 | `~/.clawdbot/stock_watcher/alerts.json` |

### watchlist.txt 格式

```
603916|苏博特
002475|立讯精密
```

## 脚本说明

| 脚本 | 功能 |
|------|------|
| `add_stock.py` | 添加股票到自选股 |
| `remove_stock.py` | 从自选股删除 |
| `list_stocks.py` | 列出所有自选股 |
| `clear_watchlist.py` | 清空自选股 |
| `manage_alerts.py` | 管理预警规则 |
| `check_alerts.py` | 检查预警 + 涨跌停检测 |
| `summarize_performance.py` | 行情摘要 + 自动预警检查 |
| `config.py` | 统一配置文件 |

## 安装

```bash
./install.sh
pip3 install -r requirements.txt
```

## 数据源

- **东方财富 API**: `https://quote.eastmoney.com/`
- 支持沪深A股及科创板
- 数据延迟约 1-3 分钟

## 安装 OpenClaw

如果你还没有安装 OpenClaw，请从 https://docs.openclaw.ai 获取安装指南。

## 注意事项

- 股票代码为 6 位数字
- 行情数据有 1-3 分钟延迟
- 需要网络连接
- 支持 A 股市场（沪市/深市/科创板）
