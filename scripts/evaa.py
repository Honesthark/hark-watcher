# EVAA short watcher. Data: MEXC futures EVAA_USDT 1h. Plan of 2026-11-01 11:20 WAT after the 1.7369 blow-off wick (08:00 WAT) dumped to ~1.31.
# Setup A: bounce into 1.40-1.46 rejected (1h wick into zone, closes red below 1.38). Momentum: 1h close above 1.46 kills the idea.
import json,urllib.request,datetime as dt,os,time
ST="state/evaa.json"
u=f"https://contract.mexc.com/api/v1/contract/kline/EVAA_USDT?interval=Min60&start={int(time.time())-3600*12}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time(); closed=[k for k in ks if k[0]+3600<=now]
first=not os.path.exists(ST)
s=json.load(open(ST)) if not first else {"last":closed[-1][0]}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+3600,W).strftime("%H:%M WAT")
active=now<dt.datetime(2026,11,8,23,0,tzinfo=W).timestamp()
for k in closed:
    if k[0]<=s["last"]: continue
    o,h,c=k[1],k[2],k[4]
    if active and not s.get("dead"):
        if h>=1.40 and c<1.38 and c<o:
            print(f"ALERT REJECTION: 1h candle {f(k)} wicked to {h} and closed red at {c}, rejected at 1.40-1.46. Short plan: entry ~1.38, SL above 1.49, TP1 1.28, TP2 1.21.")
        if c>1.46:
            s["dead"]=True
            print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 1.46. Bounce-short idea invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
