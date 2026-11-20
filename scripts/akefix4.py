# AKE post-dump shorts (user "yeah" 2026-11-20 10:25 WAT). AKE ~0.0055 after -47% day, funding negative. Nov 21 ~2.1B unlock.
# A bounce-fail: after a closed 15m candle tags 0.0066+, short on a closed 15m close under 0.0062. Entry 0.0062-0.0064, SL 0.0074, TP1 0.0050, TP2 0.0043. A 1h close above 0.0074 cancels A.
# B breakdown: closed 1h candle closes under 0.0050. Entry 0.0049-0.0050, SL 0.0058, TP1 0.0042, TP2 0.0036.
# Expires Mon 2026-11-23 07:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix4.json"; START = 1795166100; EXP = 1795413600
s = json.load(open(ST)) if os.path.exists(ST) else {"l15": START, "l60": START - 900, "tag": False, "a": False, "b": False, "ha": False}
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
        if s["a"]: continue
        if h >= 0.0066 and not s["tag"]:
            s["tag"] = True
            if c >= 0.0062: print(f"ALERT BREAK: AKE bounced to {h} ({f(t, 900)}). Setup A arms: short only on a 15m close back under 0.0062."); continue
        if s["tag"] and c < 0.0062:
            print(f"ALERT SETUP SHORT: Bounce failed. AKE tagged 0.0066+ then the 15m candle {f(t, 900)} closed at {c}, back under 0.0062. Short plan: entry 0.0062-0.0064, SL 0.0074, TP1 0.0050, TP2 0.0043."); s["a"] = True
    d = g(f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={now - 12 * 3600}&end={now}")
    for t, c in zip(d["time"], d["close"]):
        if t < s["l60"] or t + 3600 > now: continue
        s["l60"] = t + 1
        if not s["a"] and c > 0.0074:
            print(f"INVALID: 1h candle {f(t, 3600)} closed at {c}, above 0.0074. AKE bounce-fail short (A) cancelled; breakdown (B) stays armed."); s["a"] = True
        if not s["b"] and c < 0.0050:
            print(f"ALERT SETUP SHORT: Breakdown. AKE 1h candle {f(t, 3600)} closed at {c}, under 0.0050. Short plan: entry 0.0049-0.0050, SL 0.0058, TP1 0.0042, TP2 0.0036."); s["b"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
