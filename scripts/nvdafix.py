# NVDA intraday fixed setups (user-approved 2026-11-06 16:12 WAT). MEXC NVIDIA_USDT 15m. Expires 22:00 WAT today (US close).
# LONG: a closed 15m candle dips to 192.3 or lower (but stays above 191.4) and closes at 192.5+. Entry 192.3-192.8, SL 191.4, TP1 194.9, TP2 197.
# SHORT: a closed 15m candle closes below 190.0. Entry 189.6-190.0, SL 191.3, TP1 188, TP2 186. Each fires once.
import json, os, time, urllib.request, datetime as dt
ST = "state/nvdafix.json"; EXP = 1793998800
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793977199, "long": False, "short": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/NVIDIA_USDT?interval=Min15&start={int(time.time()) - 6 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] > x[2] and x[0] + 900 <= time.time()]
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not s["long"] and 191.4 < l <= 192.3 and c >= 192.5:
            print(f"ALERT SETUP LONG: 15m candle {f(t)} dipped to {l} and closed at {c}, 192 held. Long plan: entry 192.3-192.8, SL 191.4, TP1 194.9, TP2 197."); s["long"] = True
        if not s["short"] and c < 190.0:
            print(f"ALERT SETUP SHORT: 15m candle {f(t)} closed at {c}, below today's 190.0 low. Short plan: entry 189.6-190.0, SL 191.3, TP1 188, TP2 186."); s["short"] = True
json.dump(s, open(ST, "w"))
print("live", k[-1][3] if k else "?")
