# AKE fixed short setup (user-approved 2026-11-06 05:43 WAT). Expires 2026-11-08 06:00 WAT.
# Trigger: a closed 1h candle wicks to 0.0039+ and closes below 0.0037 -> short. Cancel: a 1h close above 0.0041.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix.json"; EXP = 1794114000  # 2026-11-08 06:00 WAT
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793937600, "done": False}  # from 2026-11-06 05:00 WAT bar
u = f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c > 0.0041:
            print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.0041. AKE short setup cancelled, squeeze still on."); s["done"] = True; break
        if h >= 0.0039 and c < 0.0037:
            print(f"ALERT SETUP A: 1h candle {f(t)} wicked to {h} and closed at {c}, rejected at the 0.0039-0.0041 ceiling. Short plan: entry 0.0036-0.0037, SL above 0.0042, TP1 0.0033, TP2 0.0028."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
