# UAI fixed short after 3.9M UAI (~$792k) hit Gate + MEXC on 2026-11-06 ~14:30 WAT. Set 14:40 WAT, expires 2026-11-08 06:00 WAT.
# Trigger: a closed 1h candle below 0.194 -> short. Cancel: a 1h close above 0.23 (new high, sellers absorbed).
import json, os, time, urllib.request, datetime as dt
ST = "state/uaifix.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793970000, "done": False}  # count from the 14:00 WAT bar on
u = f"https://contract.mexc.com/api/v1/contract/kline/UAI_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
if not s["done"] and time.time() < EXP:
    for t, c in zip(d["time"], d["close"]):
        if t + 3600 > time.time() or t < s["last"]: continue
        s["last"] = t + 1
        if c > 0.23:
            print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.23. UAI short cancelled, buyers absorbed the 3.9M deposit."); s["done"] = True; break
        if c < 0.194:
            print(f"ALERT SETUP A: 1h candle {f(t)} closed at {c}, below 0.194 after 3.9M UAI hit Gate + MEXC. Short plan: entry 0.192-0.194, SL above 0.2065, TP1 0.175, TP2 0.165."); s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
