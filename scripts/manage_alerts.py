#!/usr/bin/env python3
"""
Manage stock price alerts.
Usage:
    python3 manage_alerts.py add <code> [--above <price>] [--below <price>] [--pct-above <pct>] [--pct-below <pct>] [--once]
    python3 manage_alerts.py remove <code> [--above] [--below] [--pct-above] [--pct-below]]
    python3 manage_alerts.py list
    python3 manage_alerts.py clear
"""
import argparse
import json
import os
import sys

from config import ALERTS_FILE, WATCHLIST_FILE


def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return {}
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return {}
    stocks = {}
    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "|" in line:
                code, name = line.split("|", 1)
                stocks[code.strip()] = name.strip()
    return stocks


def cmd_add(args):
    alerts = load_alerts()
    watchlist = load_watchlist()

    code = args.code
    if code not in watchlist:
        print(f"⚠ {code} 不在自选股列表中，请先添加股票。")
        sys.exit(1)

    if code not in alerts:
        alerts[code] = {"name": watchlist[code]}

    alert = alerts[code]
    updated = False

    if args.above is not None:
        alert["above"] = args.above
        updated = True
    if args.below is not None:
        alert["below"] = args.below
        updated = True
    if args.pct_above is not None:
        alert["pct_above"] = args.pct_above
        updated = True
    if args.pct_below is not None:
        alert["pct_below"] = args.pct_below
        updated = True

    if args.once:
        alert["once"] = True
        updated = True

    if not updated:
        print("请至少指定一个预警条件：--above / --below / --pct-above / --pct-below")
        sys.exit(1)

    save_alerts(alerts)
    print(f"✅ 已设置 {watchlist[code]}({code}) 的预警规则：")
    print_alert_rules(code, alert)


def print_alert_rules(code, alert):
    name = alert.get("name", "")
    parts = [f"  {code} {name}"]
    if "above" in alert:
        parts.append(f"    价格上限: ¥{alert['above']:.2f}")
    if "below" in alert:
        parts.append(f"    价格下限: ¥{alert['below']:.2f}")
    if "pct_above" in alert:
        parts.append(f"    涨幅上限: {alert['pct_above']:+.2f}%")
    if "pct_below" in alert:
        parts.append(f"    跌幅下限: {alert['pct_below']:+.2f}%")
    if alert.get("once"):
        parts.append(f"    触发后自动删除: 是")
    else:
        parts.append(f"    触发后自动删除: 否")
    print("\n".join(parts))


def cmd_remove(args):
    alerts = load_alerts()
    code = args.code

    if code not in alerts:
        print(f"⚠ {code} 没有预警规则。")
        return

    alert = alerts[code]
    removed = False

    # 如果没指定具体条件，删除整个预警
    if not any([args.above, args.below, args.pct_above, args.pct_below]):
        del alerts[code]
        print(f"✅ 已删除 {code} 的所有预警规则。")
        removed = True
    else:
        if args.above and "above" in alert:
            del alert["above"]
            removed = True
        if args.below and "below" in alert:
            del alert["below"]
            removed = True
        if args.pct_above and "pct_above" in alert:
            del alert["pct_above"]
            removed = True
        if args.pct_below and "pct_below" in alert:
            del alert["pct_below"]
            removed = True

        if not removed:
            print(f"⚠ {code} 没有匹配的预警条件。")
        else:
            # 如果所有条件都删了，删除整个条目
            if not any(k in alert for k in ["above", "below", "pct_above", "pct_below"]):
                del alerts[code]
            save_alerts(alerts)
            print(f"✅ 已删除 {code} 的指定预警条件。")

    save_alerts(alerts)


def cmd_list(args):
    alerts = load_alerts()
    if not alerts:
        print("当前没有预警规则。")
        return

    print(f"📋 预警规则（共 {len(alerts)} 只）")
    print("=" * 45)
    for code, alert in alerts.items():
        print_alert_rules(code, alert)
    print("=" * 45)


def cmd_clear(args):
    save_alerts({})
    print("✅ 已清空所有预警规则。")


def main():
    parser = argparse.ArgumentParser(description="管理股票价格预警")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="添加预警规则")
    p_add.add_argument("code", help="股票代码")
    p_add.add_argument("--above", type=float, help="价格上限（超过触发）")
    p_add.add_argument("--below", type=float, help="价格下限（跌破触发）")
    p_add.add_argument("--pct-above", type=float, help="涨幅上限（%）")
    p_add.add_argument("--pct-below", type=float, help="跌幅下限（%）")
    p_add.add_argument("--once", action="store_true", help="触发后自动删除")

    # remove
    p_rm = sub.add_parser("remove", help="删除预警规则")
    p_rm.add_argument("code", help="股票代码")
    p_rm.add_argument("--above", action="store_true", help="只删除价格上限")
    p_rm.add_argument("--below", action="store_true", help="只删除价格下限")
    p_rm.add_argument("--pct-above", action="store_true", help="只删除涨幅上限")
    p_rm.add_argument("--pct-below", action="store_true", help="只删除跌幅下限")

    # list
    sub.add_parser("list", help="查看所有预警规则")

    # clear
    sub.add_parser("clear", help="清空所有预警规则")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {"add": cmd_add, "remove": cmd_remove, "list": cmd_list, "clear": cmd_clear}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
