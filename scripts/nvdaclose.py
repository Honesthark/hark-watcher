# NVDA post-close reversal (MEXC NVIDIA_USDT perp). Weekdays, fires from 15:59 New York time (21:59 WAT in US winter time, 20:59 in summer) so the user can position before the close; window ends 16:30.
# Indicator: the 15:00->16:00 ET move (last hour into the US close). Up -> SHORT, down -> LONG. Hold 1 hour, SL 1%, TP1 1%, TP2 1.5%.
# Backtest Dec 2025-Nov 2026 (perp, entry 16:05 ET, 1h exit): 151W-73L (67%), avg +0.11%/trade before leverage. Index: train 70%, test 59% (16:00 entry).
import json, os, sys, time, urllib.request, datetime as dt
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
S = "state/nvdaclose.json"
st = json.load(open(S)) if os.path.exists(S) else {}
now = dt.datetime.now(NY)
m = now.hour * 60 + now.minute
if now.weekday() > 4 or not (959 <= m < 990) or st.get("d") == str(now.date()):
    sys.exit()
try:
    u = f"https://contract.mexc.com/api/v1/contract/kline/NVIDIA_USDT?interval=Min5&start={int(time.time()) - 3 * 3600}"
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
except Exception as e:
    print("ERR", e, file=sys.stderr); sys.exit()
bars = {t + 300: c for t, c in zip(d["time"], d["close"]) if t + 300 <= time.time()}
close_t = int(now.replace(hour=16, minute=0, second=0, microsecond=0).timestamp())
c15 = bars.get(close_t - 3600)
try:  # live last price (the 15:59 read stands in for the 16:00 close)
    tk = json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=NVIDIA_USDT", headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
    live = float(tk["lastPrice"])
except Exception:
    live = bars[max(bars)] if bars else None
c16 = bars.get(close_t) or live
if not c16 or not c15 or not live or c16 == c15:
    print("closerev: missing bars"); sys.exit()
mv = c16 / c15 - 1
side = "SHORT" if mv > 0 else "LONG"; dd = 1 if side == "LONG" else -1
st["d"] = str(now.date()); json.dump(st, open(S, "w"))
exp = int(time.time()) + 3600
wat = lambda ts: time.strftime("%H:%M", time.gmtime(ts + 3600))
print(f"CLOSEREV {side} move {mv*100:+.2f} c15 {c15:.2f} c16 {c16:.2f} entry {live:.2f} SL {live*(1-dd*0.01):.2f} TP1 {live*(1+dd*0.01):.2f} TP2 {live*(1+dd*0.015):.2f} exp {exp} exit {wat(exp)}")
