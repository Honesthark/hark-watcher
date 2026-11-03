# AKE (BSC) short watcher + whale-wallet sell watch. Plan of 2026-11-02 16:47 WAT at 0.00539 after -41% day, -82% week.
# Price data: MEXC futures AKE_USDT 1h. Wallets: 13 big holders (25.8% of supply) the user flagged; 2 started selling on Nov 2.
import json,urllib.request,datetime as dt,os,time
ST="state/ake.json"
UA={"User-Agent":"Mozilla/5.0"}
u=f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min60&start={int(time.time())-3600*8}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time()
closed=[k for k in ks if k[0]+3600<=now]
first=not os.path.exists(ST)
s=json.load(open(ST)) if not first else {"last":closed[-1][0],"broken":False,"bal":{}}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+3600,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=k[2],k[4]
    if 0.0059<=h<=0.0066 and c<0.0058:
        print(f"ALERT REJECTION: 1h candle {f(k)} wicked to {h} and closed at {c}, bounce rejected at 0.0059-0.0065. Short plan: entry ~0.0057, SL above 0.0066, TP1 0.0050, TP2 0.0045.")
    if not s["broken"]:
        if c<0.00524:
            s["broken"]=True; print(f"ALERT BREAK: 1h candle {f(k)} closed at {c}, below 0.00524 (Nov 2 low). Heads-up only; watching for a failed retest of 0.0052.")
    else:
        if c>0.0058:
            s["broken"]=False; print(f"INVALID: 1h candle {f(k)} closed back above 0.0058 at {c}. Breakdown reclaimed, setup B reset.")
        elif h>=0.0052 and c<0.00524 and c>=0.0048:
            print(f"ALERT RETEST FAILED: 1h candle {f(k)} wicked to {h} and closed at {c}, below 0.00524. Short plan: entry ~0.0052, SL above 0.0058, TP1 0.0048, TP2 0.0044.")
    if c>0.0066: print(f"MOMENTUM: 1h candle {f(k)} closed at {c}, above 0.0066. Short ideas invalid, stay out.")
    s["last"]=k[0]

# ---- whale wallets: alert when a balance drops (or jumps) by 5M+ AKE since the last run ----
TOKEN="0x2c3a8Ee94dDD97244a93Bc48298f97d2C412F7Db"
WALLETS="""0x4f70fF8dd69BB0d11De2f93027Fc2F806ed635DA 0xD16f2977BDf363039aF059BC98504fC44D38d746 0x0a555aBaea3d3AD75b2B3Ce5dF866388da798fB9
0x93fc44caC166647FA7c2e014B47B9e25c1f987d7 0xB8210c25df20921538eA35729Badc3e0A63520f1 0x57114155891605D9c5a2907e2B702cF60AB07c0e
0x3E2BD24eA2aabf4311C3cA61bF5Ce290fF52a448 0x55a3319b1cFE8B82Cacb0b5cF96C7445Bf12066a 0xA9578b2b9dDCD0465cDc05140b3821032B5A722B
0xD6Bea0fFFC1cB09412Bd2dCFb8537aE78aA3cBAd 0x76e3A78017467dc174B4EE4425cbc3Fa07ce015F 0xaf6bC591Cd10E62c74497Bd5F9904329EcB59da1
0x33ab2B0C6908E472CB9F5b04E6D2a1E7E9220b4a""".split()
RPCS=["https://bsc-rpc.publicnode.com","https://bsc-dataseed.bnbchain.org","https://bsc-dataseed1.defibit.io"]
def bal(w):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":TOKEN,"data":"0x70a08231"+w[2:].lower().rjust(64,"0")},"latest"]}).encode()
    for r in RPCS:
        try:
            req=urllib.request.Request(r,body,{"Content-Type":"application/json",**UA})
            return int(json.load(urllib.request.urlopen(req,timeout=15))["result"],16)/1e18
        except Exception: continue
    return None
live=float(ks[-1][4])
try:
    tk=json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=AKE_USDT",headers=UA),timeout=15))["data"]
    ind=f"{float(tk['riseFallRate'])*100:+.1f} {float(tk['fundingRate'])*100:+.4f}"
except Exception: ind="na na"
for w in WALLETS:
    b=bal(w)
    if b is None: continue
    old=s["bal"].get(w); s["bal"][w]=b
    if old is None: continue
    dlt=b-old
    if abs(dlt)>=5e6:
        rest=sum(s["bal"].values())
        print(f"WHALE {'SELL' if dlt<0 else 'BUY'} {w} {abs(dlt):.0f} {b:.0f} {abs(dlt)*live:.0f} {rest:.0f} {ind}")
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
