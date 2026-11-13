# AGT pullback short (user's own setup, 2026-11-13 06:41 WAT, "yes" to add). Price 0.0504 after 0.024->0.0876 pump, 24h low 0.04627.
# A (rejection): a closed 1h candle trades 0.052+ (under 0.0605) and closes back under 0.052. Entry 0.052-0.054, SL 0.0605, TP1 0.0475, TP2 0.038. Cancel on a 1h close above 0.0605.
# Heads-up once when price is 0.051-0.052. Expires Mon 2026-11-16 07:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/agtfix.json"; EXP = 1794808800
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794546000 - 3600, "a": False, "ha": False}
H = {"User-Agent": "curl/8.5.0"}
u = f"https://contract.mexc.com/api/v1/contract/kline/AGT_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] >= x[2] and x[0] + 3600 <= time.time()]
try: live = float(json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=AGT_USDT", headers=H), timeout=20))["data"]["lastPrice"])
except Exception: live = k[-1][3] if k else None
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.0605:
                print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.0605. AGT pullback short cancelled."); s["a"] = True
            elif 0.052 <= h < 0.0605 and c < 0.052:
                print(f"ALERT SETUP SHORT: 1h candle {f(t)} bounced to {h} and got rejected, closing at {c} under 0.052. Max 3x, small (stop is ~14% away). Short plan: entry 0.052-0.054, SL 0.0605, TP1 0.0475, TP2 0.038."); s["a"] = True
    if live and not s["a"] and not s["ha"] and 0.051 <= live < 0.052:
        print(f"ALERT BREAK: AGT at {live}, near the 0.052-0.054 entry zone. Get ready; short only if a 1h candle closes back under 0.052."); s["ha"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
