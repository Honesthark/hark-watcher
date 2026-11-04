# STRK short watcher + whale-wallet watch. Plan of 2026-11-04 09:25 WAT after 30M STRK (~$1.32M) went from
# 0x6FC7...A218 to a Bybit deposit at 08:21 UTC. Price data: MEXC futures STRK_USDT. Wallet: STRK ERC-20 on Ethereum.
import json,urllib.request,datetime as dt,os,time
ST="state/strk.json"
UA={"User-Agent":"Mozilla/5.0"}
u=f"https://contract.mexc.com/api/v1/contract/kline/STRK_USDT?interval=Min15&start={int(time.time())-3600*8}"
d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15))["data"]
ks=list(zip(d["time"],d["open"],d["high"],d["low"],d["close"]))
now=time.time()
closed=[k for k in ks if k[0]+900<=now]
s=json.load(open(ST)) if os.path.exists(ST) else {}
if s.get("plan")!="s1104": s={"last":closed[-1][0],"plan":"s1104","b2":False,"bal":s.get("bal",{})}
W=dt.timezone(dt.timedelta(hours=1))
f=lambda k,n=900:dt.datetime.fromtimestamp(k[0]+900-n,W).strftime("%a %H:%M")+"-"+dt.datetime.fromtimestamp(k[0]+900,W).strftime("%H:%M WAT")
for k in closed:
    if k[0]<=s["last"]: continue
    h,c=k[2],k[4]
    # A: pop into 0.044-0.045 resistance (Nov 3 high 0.0452) rejected on the 15m
    if 0.0440<=h<0.0466 and 0.0420<=c<0.0436:
        print(f"ALERT REJECTION: 15m candle {f(k)} pushed to {h} (0.044-0.045 resistance) and closed back at {c}. Short plan: entry ~0.0440, SL above 0.0466, TP1 0.0415, TP2 0.0400.")
    if (k[0]+900)%3600==0:
        # B: 1h close below 0.0400 support, short the breakdown once until reclaimed
        if not s["b2"] and c<0.0400:
            s["b2"]=True; print(f"ALERT BREAKDOWN: 1h close {f(k,3600)} at {c}, below 0.0400 support. Short plan: entry ~0.0398, SL above 0.0418, TP1 0.0380, TP2 0.0365.")
        elif s["b2"] and c>0.0418:
            s["b2"]=False; print(f"INVALID: 1h close {f(k,3600)} back above 0.0418 at {c}. Breakdown reclaimed, setup B reset.")
        if c>0.0466: print(f"MOMENTUM: 1h close {f(k,3600)} at {c}, above 0.0466. Short ideas invalid, stay out.")
    s["last"]=k[0]

# ---- whale wallet: alert when its STRK balance moves by 1M+ since the last run ----
TOKEN="0xCa14007Eff0dB1f8135f4C25B34De49AB0d42766"
WALLETS=["0x6FC7332ab908517E2d251D49054a944763e9A218"]
RPCS=["https://ethereum-rpc.publicnode.com","https://eth.llamarpc.com","https://rpc.ankr.com/eth"]
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
    tk=json.load(urllib.request.urlopen(urllib.request.Request("https://contract.mexc.com/api/v1/contract/ticker?symbol=STRK_USDT",headers=UA),timeout=15))["data"]
    ind=f"{float(tk['riseFallRate'])*100:+.1f} {float(tk['fundingRate'])*100:+.4f}"
except Exception: ind="na na"
START={"0x6FC7332ab908517E2d251D49054a944763e9A218":30000005}  # ~30M before the Nov 4 08:21 UTC Bybit deposit
for w in WALLETS:
    b=bal(w)
    if b is None: continue
    old=s["bal"].get(w); s["bal"][w]=b
    if old is None: continue
    dlt=b-old
    if abs(dlt)>=1e6:
        print(f"WHALE {'SELL' if dlt<0 else 'BUY'} {w} {abs(dlt):.0f} {b:.0f} {abs(dlt)*live:.0f} {sum(s['bal'].values()):.0f} {ind} {START.get(w,0)}")
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
