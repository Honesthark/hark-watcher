# JCT squeeze-fade short (user asked 2026-11-08 21:14 WAT). Price 0.0177 after a spike to 0.021327; funding +0.56%.
# Trigger: a 1h candle closes under 0.015 -> short. Cancel: a 1h close above 0.0215 (squeeze still running). Expires 2026-11-09 17:00 WAT (unlock).
import json, os, time, urllib.request, datetime as dt
ST = "state/jctfix.json"; EXP = 1794240000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794164400, "done": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/JCT_USDT?interval=Min60&start={int(time.time()) - 8 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, c in zip(d["time"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c > 0.0215:
            print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.0215. Squeeze still running, JCT short cancelled."); s["done"] = True; break
        if c < 0.015:
            print(f"ALERT SETUP SHORT: 1h candle {f(t)} closed at {c}, back under 0.015 after the squeeze. 3x max, tiny size. TP3 0.0100. Short plan: entry 0.0145-0.0150, SL 0.0165, TP1 0.0130, TP2 0.0115."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
