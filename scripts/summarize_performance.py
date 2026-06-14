#!/usr/bin/env python3
"""
Summarize the performance of all stocks in the watchlist.
Uses East Money (东方财富) API for fast, reliable JSON data.
Automatically checks price alerts after displaying quotes.
"""
import os
import sys
import json
import requests
import time
import subprocess

from config import WATCHLIST_FILE, ALERTS_FILE

# ── East Money API helpers ──────────────────────────────────

def get_secid(code):
    """Convert 6-digit stock code to East Money secid format."""
    if code.startswith('6') or code.startswith('9'):
        return f"1.{code}"
    else:
        return f"0.{code}"

def fetch_stock_data(code, name):
    """Fetch stock data from East Money API."""
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
        return {
            "code": code,
            "name": name,
            "price": d.get("f43", 0) / 100,
            "open": d.get("f46", 0) / 100,
            "high": d.get("f44", 0) / 100,
            "low": d.get("f45", 0) / 100,
            "prev_close": d.get("f60", 0) / 100,
            "volume": d.get("f47", 0),
            "amount": d.get("f48", 0),
            "change": d.get("f169", 0) / 100,
            "pct_change": d.get("f170", 0) / 100,
            "turnover": d.get("f168", 0) / 100,
            "pe": d.get("f162", 0) / 100,
            "pb": d.get("f171", 0) / 100,
            "total_mv": d.get("f116", 0),
            "float_mv": d.get("f117", 0),
        }
    except Exception as e:
        print(f"  ⚠ {code} {name}: 获取失败 - {e}", file=sys.stderr)
        return None

# ── Formatting helpers ─────────────────────────────────────

def fmt_amount(amount):
    if amount >= 1e8:
        return f"{amount/1e8:.2f}亿"
    elif amount >= 1e4:
        return f"{amount/1e4:.2f}万"
    return f"{amount:.0f}"

def fmt_mv(mv):
    if mv >= 1e8:
        return f"{mv/1e8:.2f}亿"
    elif mv >= 1e4:
        return f"{mv/1e4:.2f}万"
    return f"{mv:.0f}" if mv else "--"

# ── Alert checking ─────────────────────────────────────────

def check_alerts_inline():
    """Check alerts using check_alerts.py and return triggered messages."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_script = os.path.join(script_dir, "check_alerts.py")
    if not os.path.exists(check_script):
        return []
    try:
        result = subprocess.run(
            [sys.executable, check_script],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip()
        if output:
            print("\n" + output)
        return output
    except Exception as e:
        print(f"  ⚠ 预警检查失败: {e}", file=sys.stderr)
        return []

# ── Main ───────────────────────────────────────────────────

def summarize_performance():
    """Summarize performance of all stocks in watchlist."""
    if not os.path.exists(WATCHLIST_FILE):
        print("自选股列表不存在。")
        return

    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("自选股列表为空。")
        return

    stocks = []
    for line in lines:
        parts = line.split("|")
        if len(parts) == 2:
            stocks.append((parts[0].strip(), parts[1].strip()))

    print(f"📊 自选股行情（共 {len(stocks)} 只）")
    print("=" * 55)

    for code, name in stocks:
        data = fetch_stock_data(code, name)
        if data:
            arrow = "🔴" if data["pct_change"] >= 0 else "🟢"
            sign = "+" if data["change"] >= 0 else ""
            print(f"\n{arrow} {code} {name}")
            print(f"   最新价: ¥{data['price']:.2f}  "
                  f"{sign}{data['change']:.2f}  "
                  f"{sign}{data['pct_change']:.2f}%")
            print(f"   今开: ¥{data['open']:.2f}  "
                  f"最高: ¥{data['high']:.2f}  "
                  f"最低: ¥{data['low']:.2f}  "
                  f"昨收: ¥{data['prev_close']:.2f}")
            print(f"   成交量: {data['volume']/10000:.2f}万手  "
                  f"成交额: {fmt_amount(data['amount'])}  "
                  f"换手率: {data['turnover']:.2f}%")
            print(f"   市盈率: {data['pe']:.2f}  "
                  f"市净率: {data['pb']:.2f}  "
                  f"总市值: {fmt_mv(data['total_mv'])}  "
                  f"流通市值: {fmt_mv(data['float_mv'])}")
        else:
            print(f"\n❓ {code} {name} — 数据获取失败")

        time.sleep(0.3)

    print("\n" + "=" * 55)
    print("数据来源：东方财富")

    # ── 自动检查预警 ──
    check_alerts_inline()

if __name__ == "__main__":
    summarize_performance()
