# BIRB fixed short setups after 2M BIRB (~$219k) hit Gate on 2026-11-06 10:49 UTC. Set 2026-11-06 13:10 WAT, expires 2026-11-08 06:00 WAT.
# A: retest of the 0.117-0.123 top rejected (wick 0.117+, 1h close < 0.116). Cancelled by a 1h close > 0.125.
# B: 1h close < 0.105 (heads-up), then a failed retest of 0.105-0.108 (1h close back < 0.105). Reset by a 1h close > 0.11.
import json, os, time, urllib.request, datetime as dt
ST = "state/birbfix.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793962800, "a": False, "b": False, "broken": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/BIRB_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.125:
                print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.125. BIRB top short cancelled, buyers absorbed the Gate deposit."); s["a"] = True
            elif h >= 0.117 and c < 0.116:
                print(f"ALERT SETUP A: 1h candle {f(t)} wicked to {h} and closed at {c}, rejected under the 0.117-0.123 top. Short plan: entry 0.115-0.116, SL above 0.1245, TP1 0.1055, TP2 0.097."); s["a"] = True
        if not s["b"]:
            if not s["broken"]:
                if c < 0.105:
                    s["broken"] = True; print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, below 0.105. Heads-up only; now watching for a failed retest of 0.105-0.108.")
            elif c > 0.11:
                s["broken"] = False
            elif h >= 0.105 and c < 0.105:
                print(f"ALERT RETEST FAILED: 1h candle {f(t)} retested {h} and closed back at {c}, under 0.105. Short plan: entry 0.103-0.105, SL above 0.1095, TP1 0.0975, TP2 0.09."); s["b"] = True
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
