# UAI fixed short after 3.9M UAI (~$792k) hit Gate + MEXC on 2026-11-06 ~14:30 WAT. Set 14:40 WAT, expires 2026-11-08 06:00 WAT.
# Phase A: a closed 1h candle below 0.194 -> short. A 1h close above 0.23 cancels A and re-arms (phase B).
# Phase B (re-arm, user asked 2026-11-06 14:38): track the high since the break; a 1h close 5-8% under it = rejection -> short,
# SL 1% above that high. A drop of more than 8% in one candle is skipped (stop too wide for 10x). A new high above the old stop re-arms. Max 3 alerts.
import json, os, time, urllib.request, datetime as dt
ST = "state/uaifix.json"; EXP = 1794114000
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1793970000, "done": False}
s.setdefault("phase", "a"); s.setdefault("hi", 0); s.setdefault("wait", 0); s.setdefault("n", 0)
u = f"https://contract.mexc.com/api/v1/contract/kline/UAI_USDT?interval=Min60&start={int(time.time()) - 12 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 3600, W).strftime("%H:%M WAT")
r = lambda x: f"{x:.4f}"
if not s["done"] and time.time() < EXP:
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 3600 > time.time() or t < s["last"]: continue
        s["last"] = t + 1
        if s["phase"] == "a":
            if c > 0.23:
                print(f"ALERT BREAK: 1h candle {f(t)} closed at {c}, above 0.23. First UAI short cancelled; re-armed to watch for a rejection at the new high.")
                s["phase"] = "b"; s["hi"] = h
            elif c < 0.194:
                print(f"ALERT SETUP A: 1h candle {f(t)} closed at {c}, below 0.194 after 3.9M UAI hit Gate + MEXC. Short plan: entry 0.192-0.194, SL above 0.2065, TP1 0.175, TP2 0.165."); s["done"] = True; break
            continue
        if s["wait"]:
            if h > s["wait"]:
                s["wait"] = 0; s["hi"] = h
            continue
        s["hi"] = max(s["hi"], h); hi = s["hi"]
        if c < hi * 0.95:
            if c >= hi * 0.92:
                s["n"] += 1
                print(f"ALERT SETUP B: 1h candle {f(t)} closed at {c}, {(1 - c / hi) * 100:.1f}% under the {hi} high, rejected. Short plan: entry {r(c * 0.995)}-{r(c * 1.005)}, SL above {r(hi * 1.01)}, TP1 {r(c * 0.92)}, TP2 {r(c * 0.85)}.")
            else:
                print(f"ALERT BREAK: 1h candle {f(t)} dumped to {c}, {(1 - c / hi) * 100:.1f}% under the {hi} high in one go. Too far to short safely at 10x; skipped. Re-arms if UAI makes a new high above {r(hi * 1.01)}.")
            s["wait"] = hi * 1.01
            if s["n"] >= 3: s["done"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
