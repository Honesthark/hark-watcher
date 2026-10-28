# BTW 1h short watcher (MEXC BTWUSDT), plan of 2026-10-26 17:00 WAT. Prints events, then a live line.
import json,urllib.request,datetime as dt,os
ST="state/btw.json"
u="https://api.mexc.com/api/v3/klines?symbol=BTWUSDT&interval=60m&limit=12"
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
    # Setup A: bounce into old support 1.35-1.45 (now resistance) rejected
    if 1.35<=h<=1.50 and c<1.30:
        print(f"ALERT REJECTION: 1h candle {f(k)} wicked to {h} and closed at {c}, rejected at 1.35-1.45. Short plan: entry ~1.30-1.35, SL above 1.50, TP1 1.15, TP2 1.05.")
    # Setup B: close below 1.05 (under the 1.07 flush low), then failed retest
    if not s["broken"]:
        if c<1.05:
            s["broken"]=True; print(f"ALERT BREAK: 1h candle {f(k)} closed at {c} (below 1.05). Heads-up only; now watch for a failed retest of 1.05-1.10.")
    else:
        if c>1.10:
            s["broken"]=False; print(f"INVALID: 1h candle {f(k)} closed back above 1.10 at {c}. Breakdown reclaimed, setup B reset.")
        elif h>=1.05 and c<1.05:
            print(f"ALERT RETEST FAILED: 1h candle {f(k)} wicked to {h} and closed at {c}, below 1.05. Short plan: entry ~1.04, SL above 1.15, TP1 0.95, TP2 0.85.")
    if c>1.50: print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 1.50. Short ideas invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",r[-1][4])
