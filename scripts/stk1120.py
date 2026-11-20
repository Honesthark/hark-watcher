# Chip/memory stock-futures shorts from the Nov 20 15:00 WAT scan (user: "add them to watcher", 2026-11-20 15:50 WAT).
# Trigger = a closed 15m US-session candle (15:30-22:00 WAT, Mon-Fri) closing under the level. Cancel on a 15m close above the stop.
# If price was already under the level when armed, it must first close back above the level, then close under again (retest-fail), so no chasing.
# TP1 = 1.5R from the trigger (derived, not from the scan). Expires Mon 2026-11-23 22:00 WAT. Usage: stk1120.py MU
import json, os, sys, time, urllib.request, datetime as dt
L = {"MU": ("MUSTOCK_USDT", "Micron", 652, 700), "STX": ("STXSTOCK_USDT", "Seagate", 483, 525), "WDC": ("WDCSTOCK_USDT", "Western Digital", 279, 300),
     "LITE": ("LITESTOCK_USDT", "Lumentum", 498, 540), "AMD": ("AMDSTOCK_USDT", "AMD", 452, 490)}
k0 = sys.argv[1]; sym, name, trg, sl = L[k0]; tp1 = round(trg - 1.5 * (sl - trg), 2)
ST = f"state/stk1120_{k0}.json"; START = 1795185900; EXP = 1795467600
H = {"User-Agent": "curl/8.5.0"}
g = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
try: live = float(g(f"https://contract.mexc.com/api/v1/contract/ticker?symbol={sym}")["lastPrice"])
except Exception: live = None
s = json.load(open(ST)) if os.path.exists(ST) else {"last": START - 1, "done": False, "under": bool(live and live < trg), "near": False}
W = dt.timezone(dt.timedelta(hours=1)); now = time.time()
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
def sess(t):
    x = dt.datetime.fromtimestamp(t, W); m = x.hour * 60 + x.minute
    return x.weekday() < 5 and 930 <= m < 1320
if now < EXP and not s["done"]:
    d = g(f"https://contract.mexc.com/api/v1/contract/kline/{sym}?interval=Min15&start={int(now) - 6 * 3600}&end={int(now)}")
    for t, c in zip(d["time"], d["close"]):
        if t <= s["last"] or t + 900 > now: continue
        s["last"] = t
        if not sess(t) or s["done"]: continue
        if c > sl:
            print(f"INVALID: {name} 15m candle {f(t)} closed at {c}, above the {sl} stop. Short setup cancelled."); s["done"] = True; continue
        if s["under"]:
            if c >= trg: s["under"] = False
            continue
        if c < trg:
            print(f"ALERT SETUP SHORT: {name} 15m candle {f(t)} closed at {c}, under {trg}. 3-5x, small. Short plan: entry near {trg}, SL {sl}, TP1 {tp1} (1.5R)."); s["done"] = True
    if live and not s["done"] and not s["under"] and not s["near"] and sess(now) and trg < live <= trg * 1.006:
        print(f"ALERT BREAK: {name} at {live}, close to {trg}. Short only on a 15m close under {trg}."); s["near"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
