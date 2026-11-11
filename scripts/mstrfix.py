# MSTR shorts after MSCI said (2026-11-11 ~23:00 WAT) it will drop Strategy from its indexes, effective Nov 30 close.
# User asked 2026-11-11 23:35 WAT. After hours ~120.5 vs 122.35 close. Only US-session candles count (15:30-22:00 WAT, Mon-Fri).
# A (rejection): a closed 15m candle trades 124.0+ (under 126.5) and closes back under 124. Entry 124-125, SL 126.5, TP1 120, TP2 116. Cancel on a 15m close above 126.5.
# B (breakdown): a closed 15m candle closes under 120. Entry 119.5-120, SL 122.5, TP1 116, TP2 112.
# Heads-up once per level when price gets within 0.6% of 124 or 120. Expires Fri 2026-11-13 22:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/mstrfix.json"; EXP = 1794603600
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794430800, "a": False, "b": False, "ha": False, "hb": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/MSTRSTOCK_USDT?interval=Min15&start={int(time.time()) - 6 * 3600}&end={int(time.time())}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
def sess(t):
    x = dt.datetime.fromtimestamp(t, W); m = x.hour * 60 + x.minute
    return x.weekday() < 5 and 15 * 60 + 30 <= m < 22 * 60
k = [x for x in zip(d["time"], d["high"], d["low"], d["close"]) if x[1] >= x[2] and x[0] + 900 <= time.time()]
try: live = float(json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=MSTRSTOCK_USDT", headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]["lastPrice"])
except Exception: live = k[-1][3] if k else None
if time.time() < EXP:
    for t, h, l, c in k:
        if t <= s["last"]: continue
        s["last"] = t
        if not sess(t): continue
        if not s["a"]:
            if c > 126.5:
                print(f"INVALID: 15m candle {f(t)} closed at {c}, above 126.5. MSTR rejection short cancelled."); s["a"] = True
            elif 124.0 <= h < 126.5 and c < 124.0:
                print(f"ALERT SETUP SHORT: 15m candle {f(t)} bounced to {h} and got rejected, closing at {c} under 124. 3-5x, small. Short plan: entry 124-125, SL 126.5, TP1 120, TP2 116."); s["a"] = True; s["b"] = s["b"] or c < 120
        if not s["b"] and c < 120.0:
            print(f"ALERT SETUP SHORT: 15m candle {f(t)} closed at {c}, under 120 support. 3-5x, small. Short plan: entry 119.5-120, SL 122.5, TP1 116, TP2 112."); s["b"] = True
    if live and sess(time.time()):
        if not s["a"] and not s["ha"] and 123.26 <= live < 124:
            print(f"ALERT BREAK: MSTR at {live}, close to the 124 rejection zone. Get ready; short only if a 15m candle closes back under 124."); s["ha"] = True
        if not s["b"] and not s["hb"] and 120 < live <= 120.72:
            print(f"ALERT BREAK: MSTR at {live}, close to the 120 breakdown level. Get ready; short only on a 15m close under 120."); s["hb"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
