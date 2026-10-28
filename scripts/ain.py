# AIN short watcher. Data: MEXC futures AIN_USDT 1h. Plan of 2026-10-27 10:40 WAT after pump 0.038->0.1436.
import json,urllib.request,datetime as dt,os,time
ST="state/ain.json"
u=f"https://contract.mexc.com/api/v1/contract/kline/AIN_USDT?interval=Min60&start={int(time.time())-3600*12}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time(); closed=[k for k in ks if k[0]+3600<=now]
first=not os.path.exists(ST)
s=json.load(open(ST)) if not first else {"last":closed[-1][0],"blowoff":False}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+3600,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=k[2],k[4]
    if c<0.129:
        print(f"ALERT SETUP A: 1h candle {f(k)} closed at {c}, below 0.129 (top failed). Short plan: entry 0.128-0.132, SL above 0.150, TP1 0.108, TP2 0.095.")
    if h>=0.16: s["blowoff"]=True
    if s["blowoff"] and h>=0.15 and c<0.150:
        print(f"ALERT SETUP B: 1h candle {f(k)} wicked to {h} and closed at {c}, back below 0.150 (blow-off rejected). Short plan: entry ~0.148, SL above 0.175, TP1 0.129, TP2 0.108.")
        s["blowoff"]=False
    if c>0.175: print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 0.175. Short ideas invalid, stay out.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
