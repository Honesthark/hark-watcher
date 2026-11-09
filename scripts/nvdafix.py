# NVDA rejection short (user asked 2026-11-09 15:32 WAT). Opened weak after the Huang probe news: lost 175.6, low 170.9, ~172.3.
# SHORT: a closed 15m candle trades up to 175.0+ (but under 177.6) and closes back below 175.0. Entry 175.0-175.6, SL 177.6, TP1 172, TP2 170.
# Cancel on a 15m close above 177.6. Fires once. Expires 22:00 WAT today (US close).
import json, os, time, urllib.request, datetime as dt
ST = "state/nvdafix.json"; EXP = 1794258000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794233700, "short": False}
if "short" not in s or s.get("v") != 2: s = {"last": 1794233700, "short": False, "v": 2}
u = f"https://contract.mexc.com/api/v1/contract/kline/NVIDIA_USDT?interval=Min15&start={int(time.time()) - 6 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] > x[2] and x[0] + 900 <= time.time()]
if time.time() < EXP and not s["short"]:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if c > 177.6:
            print(f"INVALID: 15m candle {f(t)} closed at {c}, above 177.6. NVDA short cancelled."); s["short"] = True; break
        if 175.0 <= h < 177.6 and c < 175.0:
            print(f"ALERT SETUP SHORT: 15m candle {f(t)} bounced to {h} and got rejected, closing at {c} under 175. 3-5x, small. Short plan: entry 175.0-175.6, SL 177.6, TP1 172, TP2 170."); s["short"] = True; break
json.dump(s, open(ST, "w"))
print("live", k[-1][3] if k else "?")
