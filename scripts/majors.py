# BTC & ETH trend-breakout signals on MEXC 1h perps (long and short).
# LONG: 1h close above the prior 24h high while EMA50 > EMA200. SHORT: close below prior 24h low while EMA50 < EMA200.
# SL 2x ATR(14), TP1 1R, TP2 2R. Backtest Jun 2025-Oct 2026: BTC 230 trades 54% win, ETH 207 trades 53% win.
import json, os, sys, time, urllib.request
S = "state/majors.json"
st = json.load(open(S)) if os.path.exists(S) else {}
def ema(x, n):
    a = 2 / (n + 1); e = [x[0]]
    for v in x[1:]: e.append(e[-1] + a * (v - e[-1]))
    return e
for sym, dp, slm in [("BTC", 1, 2), ("ETH", 2, 2), ("NVIDIA", 2, 1.5)]:  # NVIDIA_USDT = NVDA stock perp; backtest Jul 2025-Nov 2026: 218 trades 50% win, ~breakeven
    try:
        u = f"https://contract.mexc.com/api/v1/contract/kline/{sym}_USDT?interval=Min60&start={int(time.time())-(1300 if sym == 'NVIDIA' else 700)*3600}"
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
    except Exception as e:
        print("ERR", sym, e, file=sys.stderr); continue
    k = [x for x in zip(d["time"], d["open"], d["high"], d["low"], d["close"]) if x[0] + 3600 <= time.time()]
    if sym == "NVIDIA": k = [x for x in k if x[2] > x[3]]  # drop flat closed-market bars
    t = [x[0] for x in k]; h = [x[2] for x in k]; l = [x[3] for x in k]; c = [x[4] for x in k]
    tr = [h[0]-l[0]] + [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    a = ema(tr, 14)[-1]; e50 = ema(c, 50)[-1]; e200 = ema(c, 200)[-1]
    hi = max(h[-25:-1]); lo = min(l[-25:-1]); cl = c[-1]
    print("live", sym, cl)
    if st.get(sym) == t[-1]: continue
    side = "LONG" if cl > hi and e50 > e200 else "SHORT" if cl < lo and e50 < e200 else None
    kind = "breakout"
    if not side and sym == "NVIDIA":
        # NVDA RSI-extreme reversion with trend: RSI14 < 30 above EMA300 -> LONG, > 70 below EMA300 -> SHORT.
        # SL 2 ATR, TP1 1 ATR. Backtest Jul 2025-Nov 2026: 46 trades, 72% hit TP1 first (train 73%, test 71%), +0.15 ATR/trade.
        g = [0] + [c[i] - c[i-1] for i in range(1, len(c))]
        up = ema([max(x, 0) for x in g], 27)[-1]; dn = ema([max(-x, 0) for x in g], 27)[-1]
        rsi = 100 - 100 / (1 + up / dn) if dn else 50; e300 = ema(c, 300)[-1]
        side = "LONG" if rsi < 30 and cl > e300 else "SHORT" if rsi > 70 and cl < e300 else None
        kind = f"rsi {rsi:.0f}"
    if not side: continue
    st[sym] = t[-1]
    dd = 1 if side == "LONG" else -1
    sl = cl - dd * (2 if kind != "breakout" else slm) * a; R = abs(cl - sl)
    if kind != "breakout": R = a  # TP1 = 1 ATR, TP2 = 2 ATR
    lvl = hi if side == "LONG" else lo
    hhmm = time.strftime("%H:%M", time.gmtime(t[-1] + 3600 + 3600))
    f = lambda v: f"{v:.{dp}f}"
    print(f"SIGNAL {sym} {side} close {f(cl)} level {f(lvl)} at {hhmm} entry {f(cl)} SL {f(sl)} TP1 {f(cl+dd*R)} TP2 {f(cl+dd*2*R)} risk {abs(cl-sl)/cl*100:.2f} kind {kind}")
json.dump(st, open(S, "w"))
