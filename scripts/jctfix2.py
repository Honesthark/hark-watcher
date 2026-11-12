# JCT shorts after the 0.005 break. User asked 2026-11-12 07:01 WAT ("okay ping me"). Price 0.0042, 24h low 0.004015.
# A (rejection): a closed 1h candle trades 0.0047+ (under 0.0053) and closes back under 0.0047. Entry 0.0047-0.0049, SL 0.0053, TP1 0.0042, TP2 0.0038. Cancel on a 1h close above 0.0053.
# B (breakdown): a closed 1h candle closes under 0.0040. Entry 0.0040-0.00405, SL 0.0044, TP1 0.0036, TP2 0.0033.
# Heads-up once per level when price is within ~2% (0.0046-0.0047 or 0.0040-0.00408). Expires Sun 2026-11-15 07:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/jctfix2.json"; EXP = 1794722400
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794463200 - 3600, "a": False, "b": False, "ha": False, "hb": False}
H = {"User-Agent": "curl/8.5.0"}
u = f"https://contract.mexc.com/api/v1/contract/kline/JCT_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] >= x[2] and x[0] + 3600 <= time.time()]
try: live = float(json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=JCT_USDT", headers=H), timeout=20))["data"]["lastPrice"])
except Exception: live = k[-1][3] if k else None
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not s["a"]:
            if c > 0.0053:
                print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.0053. JCT rejection short cancelled."); s["a"] = True
            elif 0.0047 <= h < 0.0053 and c < 0.0047:
                print(f"ALERT SETUP SHORT: 1h candle {f(t)} bounced to {h} and got rejected, closing at {c} under 0.0047. 3-5x, small. Short plan: entry 0.0047-0.0049, SL 0.0053, TP1 0.0042, TP2 0.0038."); s["a"] = True
        if not s["b"] and c < 0.0040:
            print(f"ALERT SETUP SHORT: 1h candle {f(t)} closed at {c}, under 0.0040 support. 3-5x, small. Short plan: entry 0.0040-0.00405, SL 0.0044, TP1 0.0036, TP2 0.0033."); s["b"] = True
    if live:
        if not s["a"] and not s["ha"] and 0.0046 <= live < 0.0047:
            print(f"ALERT BREAK: JCT at {live}, close to the 0.0047-0.005 rejection zone. Get ready; short only if a 1h candle closes back under 0.0047."); s["ha"] = True
        if not s["b"] and not s["hb"] and 0.0040 < live <= 0.00408:
            print(f"ALERT BREAK: JCT at {live}, close to 0.0040 support. Get ready; short only on a 1h close under 0.0040."); s["hb"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
