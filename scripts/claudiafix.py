# CLAUDIA fixed shorts, set 2026-11-08 09:10 WAT (user asked). Price 0.0076 after a 0.002 -> 0.00923 pump. 15m candles, MEXC perp.
# A: wick into 0.0088-0.0092 then 15m close < 0.0085 -> short. B: 15m close < 0.0069 -> breakdown short.
# Both cancelled by a 15m close > 0.0095. Expires 2026-11-09 09:00 WAT.
import json, os, time, urllib.request, datetime as dt
ST = "state/claudiafix.json"; EXP = 1794211200
s = json.load(open(ST)) if os.path.exists(ST) else {"last": 1794123900, "a": False, "b": False}
u = f"https://contract.mexc.com/api/v1/contract/kline/CLAUDIA_USDT?interval=Min15&start={int(time.time()) - 6 * 3600}"
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
W = dt.timezone(dt.timedelta(hours=1))
f = lambda t: dt.datetime.fromtimestamp(t, W).strftime("%a %H:%M") + "-" + dt.datetime.fromtimestamp(t + 900, W).strftime("%H:%M WAT")
if time.time() < EXP and not (s["a"] and s["b"]):
    for t, h, c in zip(d["time"], d["high"], d["close"]):
        if t + 900 > time.time() or t <= s["last"]: continue
        s["last"] = t
        if c > 0.0095:
            print(f"ALERT BREAK: 15m candle {f(t)} closed at {c}, above 0.0095. CLAUDIA shorts cancelled, momentum still up."); s["a"] = s["b"] = True; break
        if not s["a"] and h >= 0.0088 and c < 0.0085:
            print(f"ALERT SETUP A: 15m candle {f(t)} retested {h} and closed back at {c}, under 0.0085. Top failed. TP3 0.0052. Short plan: entry 0.0084-0.0085, SL above 0.0098, TP1 0.0070, TP2 0.0060."); s["a"] = s["b"] = True; break
        if not s["b"] and c < 0.0069:
            print(f"ALERT BREAKDOWN: 15m candle {f(t)} closed at {c}, under 0.0069 (below this morning's lows). Short plan: entry 0.0068-0.0069, SL above 0.0077, TP1 0.0060, TP2 0.0052."); s["a"] = s["b"] = True; break
json.dump(s, open(ST, "w"))
print("live", d["close"][-1])
