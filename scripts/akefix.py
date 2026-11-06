# AKE fixed short, re-set 2026-11-06 15:06 WAT after the +95% squeeze (old 0.0037 setup cancelled at the 05:00 close).
# 1h close < 0.0045 (heads-up), then a failed retest of 0.0045-0.0047 (1h close back < 0.0045) -> short.
# Reset by a 1h close > 0.0049. Cancelled by a 1h close > 0.0058 (new high). Expires 2026-11-08 06:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/akefix2.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793970000, "done": False, "broken": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c > 0.0058:
            print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.0058, a new high. AKE short cancelled, squeeze still on."); s["done"] = True; break
        if not s["broken"]:
            if c < 0.0045:
                s["broken"] = True; print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, below 0.0045. Heads-up only; now watching for a failed retest of 0.0045-0.0047.")
        elif c > 0.0049:
            s["broken"] = False
        elif h >= 0.0045 and c < 0.0045:
            print(f"ALERT RETEST FAILED: 1h candle {f(t)} retested {h} and closed back at {c}, under 0.0045. Short plan: entry 0.0044-0.0045, SL above 0.0048, TP1 0.0041, TP2 0.0035."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
