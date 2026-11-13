# BTW failed-bounce short after losing the Nov 3 low (0.87). User asked 2026-11-13 05:12 WAT ("add it"). Price 0.853, 24h low 0.839, funding -0.14%.
# A (rejection): a closed 1h candle trades 0.87+ (under 0.925) and closes back under 0.87. Entry 0.87-0.89, SL 0.925, TP1 0.80, TP2 0.76. Cancel on a 1h close above 0.925.
# Heads-up once when price is 0.86-0.87. Expires Sun 2026-11-15 07:00 WAT. Levels are judgment.
import json, os, time, urllib.request, datetime as dt
ST = "state/btwfix.json"; EXP = 1794722400
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794542400 - 3600, "a": False, "ha": False}
H = {"User-Agent": "curl/8.5.0"}
u = f"https://contract.mexc.com/api/v1/contract/kline/BTW_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] >= x[2] and x[0] + 3600 <= time.time()]
try: live = float(json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=BTW_USDT", headers=H), timeout=20))["data"]["lastPrice"])
except Exception: live = k[-1][3] if k else None
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.925:
                print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.925. BTW bounce short cancelled."); s["a"] = True
            elif 0.87 <= h < 0.925 and c < 0.87:
                print(f"ALERT SETUP SHORT: 1h candle {f(t)} bounced to {h} and got rejected, closing at {c} under 0.87. 3-5x, small. Short plan: entry 0.87-0.89, SL 0.925, TP1 0.80, TP2 0.76."); s["a"] = True
    if live and not s["a"] and not s["ha"] and 0.86 <= live < 0.87:
        print(f"ALERT BREAK: BTW at {live}, near the 0.87-0.89 bounce zone. Get ready; short only if a 1h candle closes back under 0.87."); s["ha"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
