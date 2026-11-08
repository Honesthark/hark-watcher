# KOR breakdown short (user's Setup B), set 2026-11-08 17:15 WAT. Price 0.00111; 0.00099 is the double-bottom 24h low (hit twice 14:00-14:30 WAT).
# Trigger: a 15m candle closes under 0.00099 -> short on the retest at 0.00097-0.000985. No cancel level given. Expires 2026-11-09 17:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/korfix2.json"; EXP = 1794240000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794152700, "done": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/KOR_USDT?interval=Min15&start={int(time.time()) - 6 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, c in zip(d["time"], d["close"]):
        if t + 900 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c < 0.00099:
            print(f"ALERT BREAKDOWN: 15m candle {f(t)} closed at {c}, under the 0.00099 floor. Wait for the retest, don't chase. TP3 0.00080, TP4 0.00078. Short plan: entry 0.00097-0.000985, SL 0.00108, TP1 0.00090, TP2 0.00085."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
