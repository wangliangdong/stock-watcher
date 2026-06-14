#!/usr/bin/env python3
"""
Check stock price alerts and send notifications.
Supports one-shot alerts (auto-delete after trigger) + limit-up/limit-down detection.

Usage:
    python3 check_alerts.py          # check and print alerts
    python3 check_alerts.py --dry-run # check without sending
"""
import json
import os
import sys
import argparse
import requests

from config import ALERTS_FILE


# ── A股涨跌停限制 ───────────────────────────────────────

def get_secid(code):
    """Convert 6-digit stock code to East Money secid format."""
    if code.startswith('6') or code.startswith('9'):
        return f"1.{code}"
    else:
        return f"0.{code}"


def get_limit_pct(code):
    """获取股票的涨跌停限制（%）。"""
    # 创业板（00开头）和科创板（688开头）：±20%
    if code.startswith('00') or code.startswith('688'):
        return 0.20
    # ST/*ST（00或300开头且名称含ST）：±5%
    # 这里用代码判断，ST需查名称，暂用默认10%
    return 0.10


def fetch_stock_data(code):
    """Fetch stock data from East Money API.
    Returns dict with price, pct_change, limit_pct, is_limit_up, is_limit_down or None.
    """
    secid = get_secid(code)
    url = "http://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": secid,
        "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f168,f169,f170,f171,f177",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://quote.eastmoney.com/"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        d = resp.json().get("data")
        if not d:
            return None

        limit_pct = get_limit_pct(code)
        price = d.get("f43", 0) / 100
        pct_change = d.get("f170", 0) / 100
        prev_close = d.get("f60", 0) / 100
        name = d.get("f58", "")

        # 涨跌停判定：当前价在涨停/跌停价的 0.5% 范围内
        limit_up_price = prev_close * (1 + limit_pct)
        limit_down_price = prev_close * (1 - limit_pct)
        is_limit_up = abs(price - limit_up_price) / prev_close < 0.005
        is_limit_down = abs(price - limit_down_price) / prev_close < 0.005

        return {
            "code": code,
            "name": name,
            "price": price,
            "pct_change": pct_change,
            "prev_close": prev_close,
            "limit_up_price": limit_up_price,
            "limit_down_price": limit_down_price,
            "is_limit_up": is_limit_up,
            "is_limit_down": is_limit_down,
            "limit_pct": limit_pct,
        }
    except Exception as e:
        print(f"  ⚠ {code}: 获取失败 - {e}", file=sys.stderr)
        return None


# ── Alert helpers ─────────────────────────────────────────

def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return {}
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)


def check_alerts(dry_run=False):
    """Check all alerts. Returns list of (code, key, message) for triggered alerts.
    One-shot alerts are auto-deleted after trigger.
    Also checks limit-up/limit-down for ALL stocks in watchlist.
    """
    alerts = load_alerts()
    triggered = []
    to_delete = []

    # ── 1. 检查用户自定义预警 ──
    for code, alert in alerts.items():
        name = alert.get("name", "")
        result = fetch_stock_data(code)
        if result is None:
            continue

        price, pct_change = result["price"], result["pct_change"]

        conditions = [
            ("above", price, alert.get("above"), "价格超过"),
            ("below", price, alert.get("below"), "价格跌破"),
            ("pct_above", pct_change, alert.get("pct_above"), "涨幅超过"),
            ("pct_below", pct_change, alert.get("pct_below"), "跌幅超过"),
        ]

        for key, actual, threshold, desc in conditions:
            if threshold is None:
                continue

            fired = False
            if key in ("above", "pct_above") and actual > threshold:
                fired = True
            elif key in ("below", "pct_below") and actual < threshold:
                fired = True

            if fired:
                msg = (f"⚠️ 股票预警触发\n"
                       f"📌 {name} ({code})\n"
                       f"📊 {desc} ¥{threshold:.2f}\n"
                       f"💰 当前价格: ¥{price:.2f}\n"
                       f"📈 涨跌幅: {pct_change:+.2f}%")
                triggered.append((code, key, msg))

                if alert.get("once"):
                    to_delete.append((code, key))

    # ── 2. 涨跌停检测（检查所有自选股，不依赖 alerts.json） ──
    watchlist_file = os.path.expanduser("~/.clawdbot/stock_watcher/watchlist.txt")
    if os.path.exists(watchlist_file):
        with open(watchlist_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "|" not in line:
                    continue
                code = line.split("|")[0].strip()
                if code in alerts:
                    continue  # 已处理，避免重复
                data = fetch_stock_data(code)
                if data is None:
                    continue
                if data["is_limit_up"]:
                    msg = (f"🔴 涨停！\n"
                           f"📌 {data['name']} ({code})\n"
                           f"💰 当前价格: ¥{data['price']:.2f}\n"
                           f"📈 涨跌幅: +{data['limit_pct']*100:.0f}%\n"
                           f"📊 涨停价: ¥{data['limit_up_price']:.2f}")
                    triggered.append((code, "limit_up", msg))
                elif data["is_limit_down"]:
                    msg = (f"🟢 跌停！\n"
                           f"📌 {data['name']} ({code})\n"
                           f"💰 当前价格: ¥{data['price']:.2f}\n"
                           f"📈 涨跌幅: -{data['limit_pct']*100:.0f}%\n"
                           f"📊 跌停价: ¥{data['limit_down_price']:.2f}")
                    triggered.append((code, "limit_down", msg))

    # Print triggered alerts
    for code, key, msg in triggered:
        if dry_run:
            print(f"[DRY RUN] {msg}")
        else:
            print(msg)

    # Auto-delete one-shot alerts
    if to_delete and not dry_run:
        alerts = load_alerts()
        for code, key in to_delete:
            if code in alerts and key in alerts[code]:
                del alerts[code][key]
                if not any(k in alerts[code] for k in ["above", "below", "pct_above", "pct_below"]):
                    del alerts[code]
                print(f"🗑️ {code} 的「{key}」预警已触发并自动删除")
        save_alerts(alerts)

    return triggered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检查股票价格预警")
    parser.add_argument("--dry-run", action="store_true", help="只检查不推送")
    args = parser.parse_args()

    triggered = check_alerts(dry_run=args.dry_run)
    if not triggered:
        print("✅ 没有预警触发。")
    else:
        print(f"\n共触发 {len(triggered)} 条预警。")
