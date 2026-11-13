# AKE blow-off fade short (Hark's setup, user "yes" 2026-11-13 16:36 WAT). Pump 0.0026 -> 0.00945 high today, last 0.00915.
# Trigger: a closed 1h candle closes under 0.0068 (back inside the 10-11 WAT range). Entry 0.0066-0.0068, SL 0.0098, TP1 0.0060, TP2 0.0050.
# Cancel on a 1h close above 0.0098. Heads-up once when price is 0.0068-0.0072. Expires Sun 2026-11-15 07:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix2.json"; EXP = 1794722400
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794582000 - 3600, "a": False, "ha": False}
H = {"User-Agent": "curl/8.5.0"}
u = f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] >= x[2] and x[0] + 3600 <= time.time()]
try: live = float(json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=AKE_USDT", headers=H), timeout=20))["data"]["lastPrice"])
except Exception: live = k[-1][3] if k else None
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.0098:
                print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.0098. AKE fade short cancelled."); s["a"] = True
            elif c < 0.0068:
                print(f"ALERT SETUP SHORT: 1h candle {f(t)} closed at {c}, back under 0.0068 after the blow-off to 0.00945. Max 3x, small (stop is ~45% away). Short plan: entry 0.0066-0.0068, SL 0.0098, TP1 0.0060, TP2 0.0050."); s["a"] = True
    if live and not s["a"] and not s["ha"] and 0.0068 <= live <= 0.0072:
        print(f"ALERT BREAK: AKE at {live}, near the 0.0068 trigger. Short only if a 1h candle closes under 0.0068."); s["ha"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
