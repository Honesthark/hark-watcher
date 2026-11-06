# UAI fixed shorts, re-set 2026-11-06 14:55 WAT after the crash from 0.2227 to 0.144 (old 0.194 trigger retired: price already gone).
# A: dead-cat bounce into 0.165-0.175 rejected (wick 0.165+, 1h close < 0.16). Cancelled by a 1h close > 0.18.
# B: 1h close < 0.14 (heads-up), then a failed retest of 0.14-0.145 (1h close back < 0.14). Reset by a 1h close > 0.15.
# Expires 2026-11-08 06:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/uaifix2.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793973599, "a": False, "b": False, "broken": False}  # from the 15:00 WAT bar
u = f"https://contract.mexc.com/api/v1/contract/kline/UAI_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.18:
                print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.18. UAI bounce short cancelled, buyers are back."); s["a"] = True
            elif h >= 0.165 and c < 0.16:
                print(f"ALERT SETUP A: 1h candle {f(t)} wicked to {h} and closed at {c}, dead-cat bounce rejected under 0.165-0.175. Short plan: entry 0.158-0.162, SL above 0.172, TP1 0.145, TP2 0.13."); s["a"] = True
        if not s["b"]:
            if not s["broken"]:
                if c < 0.14:
                    s["broken"] = True; print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, below 0.14. Heads-up only; now watching for a failed retest of 0.14-0.145.")
            elif c > 0.15:
                s["broken"] = False
            elif h >= 0.14 and c < 0.14:
                print(f"ALERT RETEST FAILED: 1h candle {f(t)} retested {h} and closed back at {c}, under 0.14. Short plan: entry 0.137-0.14, SL above 0.1475, TP1 0.128, TP2 0.12."); s["b"] = True
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
