# AKE (BSC) short watcher + whale-wallet sell watch. Plan of 2026-11-02 16:47 WAT at 0.00539 after -41% day, -82% week.
# Price data: MEXC futures AKE_USDT 15m. Wallets: 13 big holders (25.8% of supply) the user flagged; 2 started selling on Nov 2.
import json,urllib.request,datetime as dt,os,time
ST="state/ake.json"
UA={"User-Agent":"Mozilla/5.0"}
u=f"https://contract.mexc.com/api/v1/contract/kline/AKE_USDT?interval=Min15&start={int(time.time())-3600*8}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time()
closed=[k for k in ks if k[0]+900<=now]
s=json.load(open(ST)) if os.path.exists(ST) else {"bal":{}}
# Trend-short plan of 2026-11-04 06:20 WAT at 0.003106 (new lows, 1h RSI ~19). Nov 3 1h plan retired. 15m candles.
if s.get("plan")!="tr1104": s={"last":closed[-1][0],"plan":"tr1104","b2":False,"bal":s.get("bal",{})}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k:dt.datetime.fromtimestamp(k[0],W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+900,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=k[2],k[4]
    # 1: bounce into the broken 0.0033-0.0034 floor, rejected
    if 0.0033<=h<0.0035 and 0.0030<=c<0.0033:
        print(f"ALERT REJECTION: 15m candle {f(k)} bounced to {h} (old 0.0033-0.0034 floor, now ceiling) and closed back at {c}. Short plan: entry ~0.0033, SL above 0.0035, TP1 0.0029, TP2 0.0027.")
    # 2: lose 0.0030, then failed retest
    if not s["b2"]:
        if c<0.0030:
            s["b2"]=True; print(f"ALERT BREAK: 15m candle {f(k)} closed at {c}, below 0.0030. Heads-up only; watching for a failed retest of 0.0030.")
    else:
        if c>0.0033:
            s["b2"]=False; print(f"INVALID: 15m candle {f(k)} closed back above 0.0033 at {c}. Breakdown reclaimed, retest setup reset.")
        elif h>=0.00298 and c<0.0030 and c>=0.0028:
            print(f"ALERT RETEST FAILED: 15m candle {f(k)} wicked to {h} and closed at {c}, back under 0.0030. Short plan: entry ~0.0030, SL above 0.00318, TP1 0.0028, TP2 0.0026.")
    if (k[0]+900)%3600==0 and c>0.00366: print(f"MOMENTUM: 1h close {f(k)} at {c}, above 0.00366 (the 05:00 high). Short ideas invalid, stay out.")
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
START={"0x4f70fF8dd69BB0d11De2f93027Fc2F806ed635DA": 1334928634, "0xD16f2977BDf363039aF059BC98504fC44D38d746": 1091612901, "0x0a555aBaea3d3AD75b2B3Ce5dF866388da798fB9": 1740264500, "0x93fc44caC166647FA7c2e014B47B9e25c1f987d7": 231956416, "0xB8210c25df20921538eA35729Badc3e0A63520f1": 4114779999, "0x57114155891605D9c5a2907e2B702cF60AB07c0e": 3470322933, "0x3E2BD24eA2aabf4311C3cA61bF5Ce290fF52a448": 3411560337, "0x55a3319b1cFE8B82Cacb0b5cF96C7445Bf12066a": 2798680517, "0xA9578b2b9dDCD0465cDc05140b3821032B5A722B": 2449095106, "0xD6Bea0fFFC1cB09412Bd2dCFb8537aE78aA3cBAd": 1951694504, "0x76e3A78017467dc174B4EE4425cbc3Fa07ce015F": 1072470066, "0xaf6bC591Cd10E62c74497Bd5F9904329EcB59da1": 2314778794, "0x33ab2B0C6908E472CB9F5b04E6D2a1E7E9220b4a": 0}  # balances at the start of the watch (Nov 2 2026, before the first sells)
for w in WALLETS:
    b=bal(w)
    if b is None: continue
    old=s["bal"].get(w); s["bal"][w]=b
    if old is None: continue
    dlt=b-old
    if abs(dlt)>=5e6:
        rest=sum(s["bal"].values())
        print(f"WHALE {'SELL' if dlt<0 else 'BUY'} {w} {abs(dlt):.0f} {b:.0f} {abs(dlt)*live:.0f} {rest:.0f} {ind} {START.get(w,0)}")
if all(w in s["bal"] for w in WALLETS):
    print("BOARD "+json.dumps([[w,START.get(w,0),s["bal"].get(w,0)] for w in WALLETS]))
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
