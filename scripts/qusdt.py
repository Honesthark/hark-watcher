# Q (QUSDT) short watcher. Data: MEXC futures Q_USDT 15m (Bybit API is geo-blocked; MEXC tracks Bybit closely).
# Plan of 2026-10-26 18:50 WAT after pump 0.056->0.0889 and dump to ~0.057. Prints events, then a live line.
import json,urllib.request,datetime as dt,os,time
ST="state/qusdt.json"
u=f"https://contract.mexc.com/api/v1/contract/kline/Q_USDT?interval=Min15&start={int(time.time())-3600*6}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time()
closed=[k for k in ks if k[0]+900<=now]
first=not os.path.exists(ST)
s=json.load(open(ST)) if not first else {"last":closed[-1][0],"broken":False}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+900,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=k[2],k[4]
    # Setup A: dead-cat bounce into 0.065-0.072 rejected
    if 0.065<=h<=0.0725 and c<0.064:
        print(f"ALERT REJECTION: 15m candle {f(k)} wicked to {h} and closed at {c}, rejected at 0.065-0.072. Short plan: entry ~0.063-0.065, SL above 0.0725, TP1 0.058, TP2 0.055.")
    # Setup B: lose the dump-wick low 0.0555, then failed retest
    if not s["broken"]:
        if c<0.0555:
            s["broken"]=True; print(f"ALERT BREAK: 15m candle {f(k)} closed at {c}, below 0.0555 (the dump wick low). Heads-up only; watching for a failed retest of 0.0555-0.058.")
    else:
        if c>0.058:
            s["broken"]=False; print(f"INVALID: 15m candle {f(k)} closed back above 0.058 at {c}. Breakdown reclaimed, setup B reset.")
        elif h>=0.0555 and c<0.0555:
            print(f"ALERT RETEST FAILED: 15m candle {f(k)} wicked to {h} and closed at {c}, below 0.0555. Short plan: entry ~0.055, SL above 0.0595, TP1 0.052, TP2 0.0485.")
    if c>0.0725: print(f"MOMENTUM: 15m candle {f(k)} closed at {c}, above 0.0725. Short ideas invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
