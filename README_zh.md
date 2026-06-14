# Stock Watcher

个人自选股监控系统，支持价格/涨跌幅预警、自动涨跌停检测、微信推送通知。

## 功能

- ✅ **添加自选股** — 用 6 位股票代码添加
- ✅ **查看自选股列表** — 清晰格式化展示
- ✅ **移除个股** — 从自选股中删除
- ✅ **清空自选股** — 一条命令清空
- ✅ **行情摘要** — 获取所有自选股的近期表现
- ✅ **标准化存储路径** — 统一管理，不再混乱
- ✅ **价格/涨跌幅预警** — 自定义阈值触发通知
- ✅ **自动涨跌停检测** — 支持主板/科创/创业板
- ✅ **微信推送** — 预警触发直接推送到微信
- ✅ **安装/卸载脚本** — 一键安装或卸载

## 安装

新用户首次使用时会自动安装。安装脚本会创建：

- 标准化自选股目录：`~/.clawdbot/stock_watcher/`
- 自选股文件：`~/.clawdbot/stock_watcher/watchlist.txt`
- 所有脚本位于技能目录中

## 使用命令

### 添加股票
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && python3 add_stock.py 600053
```

### 查看自选股
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && python3 list_stocks.py
```

### 删除股票
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && python3 remove_stock.py 600053
```

### 清空自选股
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && python3 clear_watchlist.py
```

### 行情摘要（含预警检查）
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && python3 summarize_performance.py
```

### 管理预警
```bash
# 添加预警：苏博特价格超过15元时提醒，触发后自动删除
python3 manage_alerts.py add 603916 --above 15 --once

# 查看所有预警
python3 manage_alerts.py list

# 移除指定预警条件
python3 manage_alerts.py remove 603916 --above
```

## 数据源

- **东方财富 API** — 沪深A股、科创板实时行情
- 数据延迟约 1-3 分钟

## 文件结构

```
stock-watcher/
├── SKILL.md                 # 技能元数据和说明（中文）
├── README.md                # 项目说明（中文）
├── README_zh.md             # 项目说明（中文，即本文件）
├── .gitignore               # Git 忽略配置
├── scripts/
│   ├── config.py           # 统一配置文件
│   ├── add_stock.py        # 添加自选股
│   ├── list_stocks.py      # 列出自选股
│   ├── remove_stock.py     # 删除个股
│   ├── clear_watchlist.py  # 清空自选股
│   ├── manage_alerts.py    # 管理预警规则
│   ├── check_alerts.py     # 预警检查 + 涨跌停检测
│   ├── summarize_performance.py # 行情摘要 + 预警
│   ├── install.sh          # 安装脚本
│   └── uninstall.sh        # 卸载脚本
└── references/             # 预留参考文档目录
```

## 数据存储

所有用户数据统一存储在：
- **目录**: `~/.clawdbot/stock_watcher/`
- **自选股文件**: `~/.clawdbot/stock_watcher/watchlist.txt`

格式：`股票代码|股票名称`（如 `600053|九鼎投资`）

## 预警功能

### 价格预警
- `--above <价格>` — 超过触发
- `--below <价格>` — 跌破触发
- `--pct-above <百分比>` — 涨幅超过触发
- `--pct-below <百分比>` — 跌幅超过触发
- `--once` — 触发后自动删除（一次性预警）

### 涨跌停检测
自动检测所有自选股，无需配置：
- **主板**（6/0/3开头）：±10%
- **科创板**（688开头）：±20%
- **创业板**（00开头）：±20%

## 故障排除

### "Command not found" 错误
确保已安装 Python 3：
```bash
pip3 install requests
```

### 网络问题
数据来自东方财富 API。确保网络畅通且可访问东方财富网站。

### 权限错误
确保 `~/.clawdbot/` 目录可被用户写入。

## 卸载

完全移除技能和所有数据：
```bash
cd ~/.clawdbot/skills/stock-watcher/scripts && ./uninstall.sh
```

## 定时预警检查

项目已配置定时任务（cron），工作日上午 9:00-15:00 每 5 分钟自动检查预警，触发后通过微信推送通知。
