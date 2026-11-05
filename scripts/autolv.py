# Auto-level engine (added 2026-11-04 22:30 WAT). Levels follow price: every closed 15m candle,
# resistance = highest high of the prior 16 candles (4h), support = lowest low of the prior 16.
# Trend = close vs EMA100 (15m, ~25h). Downtrend -> short rejections at resistance; uptrend -> long dips at support.
# Heads-up on a close beyond the 8h range. Each alert type max once per 2h (breaks 3h). No shorts when funding < -0.1%.
import json,urllib.request,datetime as dt,time
UA={"User-Agent":"Mozilla/5.0"}
W=dt.timezone(dt.timedelta(hours=1))
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15))
def klines(sym,hours=60):
    d=get(f"https://contract.mexc.com/api/v1/contract/kline/{sym}_USDT?interval=Min15&start={int(time.time())-3600*hours}&end={int(time.time())}")["data"]
    return [(t,float(o),float(h),float(l),float(c)) for t,o,h,l,c in zip(d["time"],d["open"],d["high"],d["low"],d["close"])]
def funding(sym):
    try: return float(get(f"https://contract.mexc.com/api/v1/contract/ticker?symbol={sym}_USDT")["data"]["fundingRate"])
    except Exception: return 0.0
def p(x): return f"{x:.6g}"
def f(k): return dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+900,W).strftime("%H:%M WAT")
def signals(ks,i,a,fr=0.0):
    """events for closed candle ks[i]; a = state dict (rate limits). returns list of strings"""
    out=[]; k=ks[i]; t,o,h,l,c=k
    if i<40: return out  # new listings: start after 10h of 15m data
    tr=[max(x[2],ks[j-1][4])-min(x[3],ks[j-1][4]) for j,x in enumerate(ks[i-14:i+1],start=i-14)]
    atr=sum(tr[1:])/14
    j0=max(0,i-120); e=ks[j0][4]; m=2/101
    for x in ks[j0+1:i+1]: e=x[4]*m+e*(1-m)
    R=max(x[2] for x in ks[i-16:i]); S=min(x[3] for x in ks[i-16:i])
    R8=max(x[2] for x in ks[i-32:i]); S8=min(x[3] for x in ks[i-32:i])
    ok=lambda key,hrs:t-a.get(key,0)>=hrs*3600
    if c<e and h>=R-0.25*atr and c<o and c<=h-0.5*atr and fr>-0.001 and ok("rej",2):
        sl=max(h,R)+0.3*atr; r=sl-c; a["rej"]=t
        out.append(f"ALERT REJECTION: 15m candle {f(k)} tested the 4h high {p(R)} (wick to {p(h)}) and closed back at {p(c)}, trend down. Short plan: entry ~{p(c)}, SL above {p(sl)}, TP1 {p(c-r)}, TP2 {p(c-2*r)}.")
    if c>e and l<=S+0.25*atr and c>o and c>=l+0.5*atr and ok("dip",2):
        sl=min(l,S)-0.3*atr; r=c-sl; a["dip"]=t
        out.append(f"ALERT LONG DIP: 15m candle {f(k)} tested the 4h low {p(S)} (wick to {p(l)}) and closed back at {p(c)}, trend up. Long plan: entry ~{p(c)}, SL below {p(sl)}, TP1 {p(c+r)}, TP2 {p(c+2*r)}.")
    if c<S8 and ok("bdn",3):
        a["bdn"]=t; out.append(f"ALERT BREAK: 15m candle {f(k)} closed at {p(c)}, below the 8h low {p(S8)}. New lows; wait for a bounce to short, don't chase.")
    if c>R8 and ok("bup",3):
        a["bup"]=t; out.append(f"ALERT BREAK: 15m candle {f(k)} closed at {p(c)}, above the 8h high {p(R8)}. Breaking out; shorts are risky, wait for a dip to long.")
    return out
def run(sym,s):
    ks=klines(sym); now=time.time(); closed=[k for k in ks if k[0]+900<=now]
    a=s.setdefault("auto",{}); last=a.get("last") or closed[-1][0]; fr=funding(sym)
    for i,k in enumerate(closed):
        if k[0]<=last: continue
        for ev in signals(closed,i,a,fr): print(ev)
        last=k[0]
    a["last"]=last
    return ks
