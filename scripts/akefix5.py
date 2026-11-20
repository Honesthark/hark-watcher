# AKE post-unlock shorts (user "yes" 2026-11-20 21:42 WAT). Nov 21 ~01:00 WAT unlock ~2.1B AKE (~9% of float). AKE ~0.0062, ranging 0.0061-0.0070 since 17:00.
# A breakdown: closed 1h candle closes under 0.0060. Entry 0.0059-0.0060, SL 0.0067, TP1 0.0050, TP2 0.0043.
# B pop-fail: after a closed 15m candle tags 0.0070+, short on a closed 15m close back under 0.0067. Entry 0.0067-0.0069, SL 0.0078, TP1 0.0058, TP2 0.0050. A 1h close above 0.0078 cancels B.
# Expires Sun 2026-11-22 22:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix5.json"; START = 1795207500; EXP = 1795381200
s = json.load(open(ST)) if os.path.exists(ST) else {"l15": START, "l60": START - 2700, "tag": False, "a": False, "b": False}
H = {"User-Agent": "curl/8.5.0"}
now = int(time.time())
g = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t, n: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + n, W).strftime("%H:%M WAT")
try: live = float(g("https://contract.mexc.com/api/v1/contract/ticker?symbol=AKE_USDT")["lastPrice"])
except Exception: live = None
if now < EXP:
    d = g(f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min15&start={now - 6 * 3600}&end={now}")
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t < s["l15"] or t + 900 > now: continue
        s["l15"] = t + 1
        if s["b"]: continue
        if h >= 0.0070 and not s["tag"]:
            s["tag"] = True
            if c >= 0.0067: print(f"ALERT BREAK: AKE popped to {h} ({f(t, 900)}). Setup B arms: short only on a 15m close back under 0.0067."); continue
        if s["tag"] and c < 0.0067:
            print(f"ALERT SETUP SHORT: Pop failed. AKE tagged 0.0070+ then the 15m candle {f(t, 900)} closed at {c}, back under 0.0067. 3x max. Short plan: entry 0.0067-0.0069, SL 0.0078, TP1 0.0058, TP2 0.0050."); s["b"] = True
    d = g(f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={now - 12 * 3600}&end={now}")
    for t, c in zip(d["time"], d["close"]):
        if t < s["l60"] or t + 3600 > now: continue
        s["l60"] = t + 1
        if not s["b"] and c > 0.0078:
            print(f"INVALID: 1h candle {f(t, 3600)} closed at {c}, above 0.0078. AKE pop-fail short (B) cancelled; breakdown (A) stays armed."); s["b"] = True
        if not s["a"] and c < 0.0060:
            print(f"ALERT SETUP SHORT: Breakdown. AKE 1h candle {f(t, 3600)} closed at {c}, under 0.0060. 3x max. Short plan: entry 0.0059-0.0060, SL 0.0067, TP1 0.0050, TP2 0.0043."); s["a"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
