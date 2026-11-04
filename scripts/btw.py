# BTW auto-level watcher + 1h squeeze-fade (was: 1h short watcher) (MEXC BTWUSDT), plan of 2026-11-03 11:10 WAT. Prints events, then a live line.
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
    s["last"]=k[0]
# Auto levels on 15m (scripts/autolv.py, added 2026-11-04 22:30 WAT). Fixed A/B plans retired; Setup C kept to Nov 9.
import sys; sys.path.insert(0,"scripts"); import autolv
autolv.run("BTW",s)
json.dump(s,open(ST,"w"))
print("live",r[-1][4])

