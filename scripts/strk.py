# STRK auto-level watcher + whale-wallet watch. Plan of 2026-11-04 09:25 WAT after 30M STRK (~$1.32M) went from
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
# Levels follow price automatically (scripts/autolv.py, 2026-11-04 22:40 WAT). Fixed A/B plans retired.
import sys; sys.path.insert(0,"scripts"); import autolv
if s.get("plan")!="auto": s={"plan":"auto","bal":s.get("bal",{})}
autolv.run("STRK",s)

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
