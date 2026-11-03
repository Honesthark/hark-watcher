# Q (QUSDT) watcher. Data: MEXC futures Q_USDT 15m (Bybit API is geo-blocked; MEXC tracks Bybit closely).
# Plan of 2026-11-03 17:30 WAT after a squeeze 0.0282 -> 0.0314 (post Nov 2 vesting send, funding negative).
# Dip long: a 15m candle dips into 0.0295-0.0306 and closes back at/above 0.0300. Off after a 15m close below 0.0288 or after Nov 5 23:59 WAT.
import json,urllib.request,datetime as dt,os,time
ST="state/qusdt.json"
END=1793919540  # 2026-11-05 23:59 WAT
u=f"https://contract.mexc.com/api/v1/contract/kline/Q_USDT?interval=Min15&start={int(time.time())-3600*6}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time()
closed=[k for k in ks if k[0]+900<=now]
s=json.load(open(ST)) if os.path.exists(ST) else {}
if s.get("plan")!="long1103": s={"last":closed[-1][0],"plan":"long1103","dead":False}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+900,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    l,c=k[3],k[4]
    if not s["dead"] and k[0]<END:
        if c<0.0288:
            s["dead"]=True; print(f"INVALID: 15m candle {f(k)} closed at {c}, below 0.0288. Support lost, dip-long idea off.")
        elif 0.0295<=l<=0.0306 and 0.0300<=c<=0.0318:
            print(f"ALERT LONG DIP: 15m candle {f(k)} dipped to {l} and closed back at {c}, holding the 0.0300-0.0305 support after the squeeze. Long plan: entry ~0.0303, SL below 0.0288, TP1 0.033, TP2 0.035.")
    s["last"]=k[0]
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
