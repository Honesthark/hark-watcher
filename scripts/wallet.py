# Whale-wallet watch (BNB Chain), added 2026-11-05 10:58 WAT at the user's request.
# Prints WHALE lines in the same format as strk.py when a watched wallet's balance moves by MIN tokens since the last run.
# AIN 0x8047...3963 held 40.02M AIN. BTW 0x5437...B3A3 received 101.0M from 0x61D8...c9b4 and 96.4M from 0x60ad...55ad on Nov 5 ~08:37 UTC (197.4M total).
import json,urllib.request,os,sys
SYM=sys.argv[1]; ST=f"state/wallet_{SYM.lower()}.json"; UA={"User-Agent":"Mozilla/5.0"}
CFG={"AIN":("0x9558a9254890B2A8B057a789F413631B9084f4a3",1e6,{"0x8047a4b87d07a4fc844bf27f3955c90989673963":40018678}),
     "BTW":("0x444045B0EE1ee319A660a5E3d604CA0ffA35ACaA",1e6,{"0x543714F349970cD3b02d6Dc6A85ac8641f2BB3A3":197417759}),
     # UAI added 2026-11-08 10:05 WAT: Gnosis Safe 0xc79b...99c7 (95.3M left) sent 20M to 0x87b2...B7E5, which is splitting 150K chunks to fresh wallets (16.94M left).
     "UAI":("0x3e5d4f8aee0d9b3082d5f6da5d6e225d17ba9ea0",1e6,{"0x87b2b9d6b3c449ea4d03bef6d45b40ca8644b7e5":20000000,"0xc79b88ca005dff2adf31a3c191a0504a5eda99c7":115282658,
            # 2026-11-09 11:10 WAT (user asked): fresh wallet got 25M UAI from Gnosis Safe 0xAf3... at 10:06 UTC.
            "0xc1888ffccfbaef1035ee48c693df40f18cb0b7c6":25000015}),
     # JCT added 2026-11-08 13:30 WAT: Janction's five locked-allocation Safes on Ethereum, untouched since TGE 2025-11-10. Cliff ends ~2026-11-10 (calendars) or 2026-12-10 (docs).
     "JCT":("0xC477B6dfd26EC2460b3b92de18837Fd476Ea7549",20e6,{"0xa68f0255c0eeb35e3cf558d58cfbbfa8811b9b84":13145625000,"0x246d024c6816efaae060235d5695a8af31e3d562":10670000000,
            "0x250371ff899cbac4ef5156e6a3f4982a6cf10e2e":9000000000,"0xe906efef04fae94d784eaf702278657ef924a050":5000000000,"0xa13918f90296072fc15409fced346c8a423ddf86":1834375000}),
     # H (Humanity) added 2026-11-11 21:56 WAT (user asked): four never-used wallets got ~211.7M H at 21:24 WAT Nov 11 from four senders, 0 ETH for gas.
     "H":("0xe76c5b78f93909d34404e9eb4c1f19e7582a5de1",1e6,{"0x3829da7ea774e57a5332b02480c79f93d9ef13a0":41028838,"0x3a0ba545eabbd2e90061717a04547f462c2f2d8e":45163742,
            "0x4bfa4ea5cfcdd218accbd77153150c357a988a15":53000108,"0xa7fc20a7aee71da0f8ebbbcc2924500db477a7a5":72518912})}
ETH={"JCT","H"}
GASWATCH={"H"}  # ping once when a watched wallet first receives ETH for gas
TOKEN,MIN,START=CFG[SYM]
RPCS=(["https://ethereum-rpc.publicnode.com","https://eth.llamarpc.com","https://rpc.ankr.com/eth"] if SYM in ETH else
      ["https://bsc-dataseed.bnbchain.org","https://bsc-dataseed1.defibit.io","https://bsc-rpc.publicnode.com"])
def bal(w):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":TOKEN,"data":"0x70a08231"+w[2:].lower().rjust(64,"0")},"latest"]}).encode()
    for r in RPCS:
        try: return int(json.load(urllib.request.urlopen(urllib.request.Request(r,body,{"Content-Type":"application/json",**UA}),timeout=15))["result"],16)/1e18
        except Exception: continue
    return None
try:
    tk=json.load(urllib.request.urlopen(urllib.request.Request(f"https://contract.mexc.com/api/v1/contract/ticker?symbol={SYM}_USDT",headers=UA),timeout=15))["data"]
    live=float(tk["lastPrice"]); ind=f"{float(tk['riseFallRate'])*100:+.1f} {float(tk['fundingRate'])*100:+.4f}"
except Exception: live=0; ind="na na"
s=json.load(open(ST)) if os.path.exists(ST) else {}
for w in START:
    b=bal(w)
    if b is None: continue
    old=s.get(w); s[w]=b
    if old is None: continue
    dlt=b-old
    if abs(dlt)>=MIN:
        print(f"WHALE {'SELL' if dlt<0 else 'BUY'} {w} {abs(dlt):.0f} {b:.0f} {abs(dlt)*live:.0f} {sum(s.values()):.0f} {ind} {START[w]}")
if SYM in GASWATCH:
    for w in START:
        body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":[w,"latest"]}).encode()
        g=None
        for r in RPCS:
            try: g=int(json.load(urllib.request.urlopen(urllib.request.Request(r,body,{"Content-Type":"application/json",**UA}),timeout=15))["result"],16)/1e18; break
            except Exception: continue
        if g is None: continue
        k="gas:"+w; old=s.get(k); s[k]=g
        if old is not None and old<=0 and g>0: print(f"GAS {w} {g:.5f}")
json.dump(s,open(ST,"w"))
print("live",live)
