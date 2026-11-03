# BTW 1h short watcher (MEXC BTWUSDT), plan of 2026-11-03 11:10 WAT. Prints events, then a live line.
import json,urllib.request,datetime as dt,os
ST="state/btw.json"
u="https://api.mexc.com/api/v3/klines?symbol=BTWUSDT&interval=60m&limit=16"
r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15))
now=dt.datetime.now(dt.timezone.utc).timestamp()*1000
closed=[k for k in r if k[6]<=now]
first=not os.path.exists(ST)
s=json.load(open(ST)) if not first else {"last":closed[-1][0],"broken":False}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0]/1000,W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[6]/1000+0.001,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=float(k[2]),float(k[4])
    # Plan of 2026-11-03 11:10 WAT (price 0.8947, 24h low). Old 1.35-1.50 / 1.05 levels retired.
    # Setup A: bounce into 0.93-0.96 rejected, 1h close back below 0.925
    if 0.93<=h<0.96 and c<0.925:
        print(f"ALERT REJECTION: 1h candle {f(k)} wicked to {h} and closed at {c}, bounce rejected at 0.93-0.95. Short plan: entry ~0.925, SL above 0.96, TP1 0.876, TP2 0.83.")
    # Setup B: close below 0.876 (Oct 26 low), then failed retest
    if not s.get("b2"):
        if c<0.876:
            s["b2"]=True; print(f"ALERT BREAK: 1h candle {f(k)} closed at {c}, below 0.876 (Oct 26 low). Heads-up only; now watch for a failed retest of 0.872-0.876.")
    else:
        if c>0.905:
            s["b2"]=False; print(f"INVALID: 1h candle {f(k)} closed back above 0.905 at {c}. Breakdown reclaimed, setup B reset.")
        elif h>=0.872 and c<0.876:
            print(f"ALERT RETEST FAILED: 1h candle {f(k)} wicked to {h} and closed at {c}, below 0.876. Short plan: entry ~0.872, SL above 0.905, TP1 0.83, TP2 0.78.")
    # Setup C (added 2026-11-01, unlock week): short squeeze then fade.
    # Squeeze = a high >=12% above the lowest low of the 10 candles before it, within the last 4 closed candles.
    # Backtest (last 500 1h candles, one trade at a time, TP1 1R): 13W-7L, +6R.
    # Trigger = this candle closes red, below the prior candle's low, and below the squeeze high by >=3%.
    ix=[x[0] for x in closed].index(k[0])
    if ix>=6 and dt.datetime.fromtimestamp(k[0]/1000,W)<dt.datetime(2026,11,9,23,0,tzinfo=W):
        o=float(k[1]); pl=float(closed[ix-1][3])
        recent=closed[max(0,ix-3):ix+1]; sq=max(recent,key=lambda x:float(x[2])); sqh=float(sq[2])
        si=[x[0] for x in closed].index(sq[0]); base=[float(x[3]) for x in closed[max(0,si-10):si]]
        if base and sqh>=min(base)*1.12 and c<o and c<pl and c<=sqh*0.97 and s.get("c_sq")!=sq[0]:
            s["c_sq"]=sq[0]; stop=sqh*1.02; risk=stop-c
            print(f"ALERT SQUEEZE FADE: BTW squeezed to {sqh} (+{(sqh/min(base)-1)*100:.0f}% off {min(base)}), then 1h candle {f(k)} closed red at {c} below the prior low. Short plan: entry ~{c:.4f}, SL {stop:.4f} (above the squeeze high), TP1 {c-risk:.4f}, TP2 {max(c-risk*2,min(base)):.4f}. Size small, unlock-week swings are violent.")
    if c>0.986: print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 0.986. Short ideas invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",r[-1][4])
