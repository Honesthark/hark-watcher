# NVDA 15m RSI snap-back (MEXC NVIDIA_USDT). LONG: RSI14 < 25 and close above EMA1200 (uptrend). SHORT: RSI14 > 75 and close below EMA1200.
# SL 1.5 ATR, TP1 1 ATR, TP2 2 ATR runner. Backtest Mar-Nov 2026: 109 trades (~14/month), 71% hit TP1 first (train 72%, test 71%), +0.3 ATR/trade.
import json, os, sys, time, urllib.request
S = "state/nvda15.json"
st = json.load(open(S)) if os.path.exists(S) else {}
def ema(x, n):
    a = 2 / (n + 1); e = [x[0]]
    for v in x[1:]: e.append(e[-1] + a * (v - e[-1]))
    return e
K = {}; end = int(time.time())
try:
    for _ in range(2):
        s = end - 1900 * 900
        d = json.load(urllib.request.urlopen(urllib.request.Request(f"https://contract.mexc.com/api/v1/contract/kline/NVIDIA_USDT?interval=Min15&start={s}&end={end}", headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
        for x in zip(d["time"], d["open"], d["high"], d["low"], d["close"]): K[x[0]] = x
        end = s
except Exception as e:
    print("ERR", e, file=sys.stderr); sys.exit()
k = [x for x in sorted(K.values()) if x[2] > x[3] and x[0] + 900 <= time.time()]
t = [x[0] for x in k]; h = [x[2] for x in k]; l = [x[3] for x in k]; c = [x[4] for x in k]
tr = [h[0]-l[0]] + [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
a = ema(tr, 14)[-1]; g = [0] + [c[i]-c[i-1] for i in range(1, len(c))]
up = ema([max(x, 0) for x in g], 27)[-1]; dn = ema([max(-x, 0) for x in g], 27)[-1]
rsi = 100 - 100 / (1 + up / dn) if dn else 50; e = ema(c, 1200)[-1]; cl = c[-1]
print("live NVIDIA", cl, "rsi15", round(rsi, 1))
fresh = time.time() - (t[-1] + 900) < 20 * 60  # skip stale signals
side = "LONG" if rsi < 25 and cl > e else "SHORT" if rsi > 75 and cl < e else None
if side and fresh and st.get("t") != t[-1] and t[-1] - st.get("t", 0) >= 4 * 900:
    st["t"] = t[-1]; dd = 1 if side == "LONG" else -1; sl = cl - dd * 1.5 * a
    hhmm = time.strftime("%H:%M", time.gmtime(t[-1] + 900 + 3600))
    print(f"SIGNAL NVIDIA {side} close {cl:.2f} level {e:.2f} at {hhmm} entry {cl:.2f} SL {sl:.2f} TP1 {cl+dd*a:.2f} TP2 {cl+dd*2*a:.2f} risk {abs(cl-sl)/cl*100:.2f} kind rsi15 {rsi:.0f}")
json.dump(st, open(S, "w"))
