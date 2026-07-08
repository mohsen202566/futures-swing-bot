from __future__ import annotations
import argparse,json
from datetime import datetime
from database import init_db
from log_store import list_logs
from rejection_store import list_rejections
from stats_manager import format_stats
from signal_store import get_open_signals

def fmt_ts(ms): return datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H:%M:%S') if ms else '-'
def main():
    init_db(); p=argparse.ArgumentParser(description='Futures Hunt Trap VPS CLI'); sub=p.add_subparsers(dest='cmd')
    logs=sub.add_parser('logs'); logs.add_argument('--limit',type=int,default=50); logs.add_argument('--level'); logs.add_argument('--symbol')
    rej=sub.add_parser('rejects'); rej.add_argument('--limit',type=int,default=50); rej.add_argument('--symbol'); rej.add_argument('--reason'); rej.add_argument('--stage')
    sub.add_parser('stats'); sub.add_parser('open'); args=p.parse_args()
    if args.cmd=='logs':
        for r in list_logs(args.limit,args.level,args.symbol): print(f"[{fmt_ts(r['ts_ms'])}] {r['level']} | {r.get('symbol') or '-'} | {r.get('module') or '-'}\n{r['message']}\n")
    elif args.cmd=='rejects':
        for r in list_rejections(args.limit,args.symbol,args.reason,args.stage): print(f"[{fmt_ts(r['ts_ms'])}] REJECT | {r.get('symbol') or '-'} | {r['stage']} | {r['reason_code']}\n{r['reason_text']}\n")
    elif args.cmd=='stats': print(format_stats(30))
    elif args.cmd=='open':
        for r in get_open_signals(): print(f"#{r['id']} | {r['symbol']} | {r['side']} | {r['signal_type']} | entry={r['entry']} sl={r['sl']} tp={r['tp']}")
    else: p.print_help()
if __name__=='__main__': main()
