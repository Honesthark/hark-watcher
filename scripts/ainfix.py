# AIN fixed short setups after the Nov 6 crash (0.268 -> 0.12). Set 2026-11-06 06:05 WAT, expires 2026-11-08 06:00 WAT.
# A: dead-cat bounce into 0.135-0.15 rejected (1h close < 0.13). Cancelled by a 1h close > 0.16.
# B: 1h close < 0.105 (heads-up), then a failed retest of 0.105-0.112 (1h close back < 0.105).
import json, os, time, urllib.request, datetime as dt
ST = "state/ainfix.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793941200, "a": False, "b": False, "broken": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/AIN_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.16:
                print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.16. AIN bounce short cancelled."); s["a"] = True
            elif h >= 0.135 and c < 0.13:
                print(f"ALERT SETUP A: 1h candle {f(t)} wicked to {h} and closed at {c}, dead-cat bounce rejected under 0.135-0.15. Short plan: entry 0.128-0.132, SL above 0.153, TP1 0.112, TP2 0.10."); s["a"] = True
        if not s["b"]:
            if not s["broken"]:
                if c < 0.105:
                    s["broken"] = True; print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, below 0.105. Heads-up only; now watching for a failed retest of 0.105-0.112.")
            elif c > 0.115:
                s["broken"] = False
            elif h >= 0.105 and c < 0.105:
                print(f"ALERT RETEST FAILED: 1h candle {f(t)} retested {h} and closed back at {c}, under 0.105. Short plan: entry 0.103-0.105, SL above 0.115, TP1 0.095, TP2 0.086."); s["b"] = True
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
