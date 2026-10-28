# IRYS 1h short watcher (MEXC IRYSUSDT), plan of 2026-10-24 11:30 WAT. Prints events or nothing.
import json,urllib.request,datetime as dt,os
ST="state/irys.json"
u="https://api.mexc.com/api/v3/klines?symbol=IRYSUSDT&interval=60m&limit=12"
r=json.load(urllib.request.urlopen(u,timeout=15))
now=dt.datetime.now(dt.timezone.utc).timestamp()*1000
closed=[k for k in r if k[6]<=now]
s=json.load(open(ST)) if os.path.exists(ST) else {"last":0,"broken":False}
s.setdefault("broken",False)
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0]/1000,W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[6]/1000,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=float(k[2]),float(k[4])
    # Setup A: bounce into old range floor 0.074-0.082 rejected
    if 0.074<=h<=0.085 and c<0.072:
        print(f"ALERT REJECTION: 1h candle {f(k)} wicked to {h} and closed at {c}, rejected at 0.074-0.082. Short plan: entry ~0.072-0.075, SL above 0.085, TP1 0.060, TP2 0.050.")
    # Setup B: breakdown below 0.055 then failed retest
    if not s["broken"]:
        if c<0.055:
            s["broken"]=True; print(f"ALERT BREAK: 1h candle {f(k)} closed at {c} (below 0.055). Heads-up only; now watch for a failed retest of 0.055-0.058.")
    else:
        if c>0.058:
            s["broken"]=False; print(f"INVALID: 1h candle {f(k)} closed back above 0.058 at {c}. Breakdown reclaimed, setup B reset.")
        elif h>=0.055 and c<0.055:
            print(f"ALERT RETEST FAILED: 1h candle {f(k)} wicked to {h} and closed at {c}, below 0.055. Short plan: entry ~0.054, SL above 0.062, TP1 0.047, TP2 0.040.")
    if c>0.085: print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 0.085. Short ideas invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",r[-1][4])
