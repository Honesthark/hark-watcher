# AKE blow-off rejection short v2 (user "yes" 2026-11-13 17:06 WAT). akefix2 cancelled; high 0.01237, last 0.01126.
# Trigger: a closed 1h candle closes under 0.0099 (back under the 0.0099 ask). Entry 0.0097-0.0100, SL 0.0128, TP1 0.0078, TP2 0.0063.
# Cancel on a 1h close above 0.0128. Heads-up once at 0.0100-0.0105. Expires Sun 2026-11-15 07:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix3.json"; EXP = 1794722400
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794585600 - 3600, "a": False, "ha": False}
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
            if c > 0.0128:
                print(f"INVALID: 1h candle {f(t)} closed at {c}, above 0.0128. AKE rejection short cancelled."); s["a"] = True
            elif c < 0.0099:
                print(f"ALERT SETUP SHORT: 1h candle {f(t)} closed at {c}, back under 0.0099 after the blow-off to 0.01237. Max 3x, small (stop is ~30% away). Short plan: entry 0.0097-0.0100, SL 0.0128, TP1 0.0078, TP2 0.0063."); s["a"] = True
    if live and not s["a"] and not s["ha"] and 0.0100 <= live <= 0.0105:
        print(f"ALERT BREAK: AKE at {live}, near the 0.0099 trigger. Short only if a 1h candle closes under 0.0099."); s["ha"] = True
json.dump(s, open(ST, "w"))
print("live", live if live else "?")
