# KOR fixed short, set 2026-11-07 14:00 WAT from the user's levels (stop widened 0.00329 -> 0.00335 over the 0.00331 1h wick).
# Price was 0.00274, below the zone. Trigger: a 1h candle trades up into 0.0029-0.00305 and closes back under 0.0029 -> short.
# Cancelled by any 1h high >= 0.00335 (stop level) before the trigger. Expires 2026-11-09 06:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/korfix.json"; EXP = 1794200400
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794049200, "done": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/KOR_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if h >= 0.00335:
            print(f"INVALID: 1h candle {f(t)} hit {h}, at or above the 0.00335 stop before any rejection. KOR short cancelled."); s["done"] = True; break
        if h >= 0.0029 and c < 0.0029:
            print(f"ALERT SETUP SHORT: 1h candle {f(t)} bounced to {h} and closed back at {c}, under 0.0029. Extra targets TP3 0.0024, TP4 0.00215. Short plan: entry 0.0029-0.00305, SL 0.00335, TP1 0.0027, TP2 0.00256."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
