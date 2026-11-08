# KOR shorts after the 0.00155 rejection (user asked 2026-11-08 21:40 WAT). Price 0.001266.
# Setup A: a 1h candle wicks to 0.00140+ and closes back under 0.00135 -> short 0.00135-0.00140.
# Setup B: a 1h candle closes under 0.00120 -> short the retest 0.00121-0.00123.
# Cancel both on a 1h close above 0.00160. Expires 2026-11-09 17:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/korfix3.json"; EXP = 1794240000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794164400, "a": False, "b": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/KOR_USDT?interval=Min60&start={int(time.time()) - 8 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if time.time() < EXP and not (s["a"] and s["b"]):
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c > 0.0016:
            print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.00160. KOR shorts cancelled."); s["a"] = s["b"] = True; break
        if not s["a"] and h >= 0.0014 and c < 0.00135:
            print(f"ALERT SETUP A: 1h candle {f(t)} hit {h} and closed back at {c}, under 0.00135. Bounce failed. 3x, tiny. Short plan: entry 0.00135-0.00140, SL 0.00160, TP1 0.00120, TP2 0.00110."); s["a"] = s["b"] = True; break
        if not s["b"] and c < 0.0012:
            print(f"ALERT BREAKDOWN: 1h candle {f(t)} closed at {c}, under 0.00120. Wait for the retest, don't chase. 3x, tiny. Short plan: entry 0.00121-0.00123, SL 0.00137, TP1 0.00110, TP2 0.00100."); s["a"] = s["b"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
