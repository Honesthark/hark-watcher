# Watch MEXC futures gainers (>=15% 24h, >$3M vol, plus extra symbols) for short triggers on closed 1h candles.
# Trigger: 1h candle wicks within 3% of the 24h high (or makes it), closes red, upper wick >=40% of range, close below prior 1h low.
# One alert per symbol per 6h. Prints ALERT lines only for new triggers, plus a WATCH line.
import json,urllib.request,time,os
S="state/gainers.json"; EXTRA=["AIN_USDT"]
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"user-agent":"curl/8.5.0"}),timeout=20))
st=json.load(open(S)) if os.path.exists(S) else {}
now=time.time()
tk={x["symbol"]:x for x in get("https://contract.mexc.com/api/v1/contract/ticker")["data"]}
cand=[s for s,x in tk.items() if s.endswith("_USDT") and float(x.get("amount24") or 0)>3e6 and float(x["riseFallRate"])>=0.15]
cand=sorted(cand,key=lambda s:-float(tk[s]["riseFallRate"]))[:6]+[e for e in EXTRA if e in tk]
seen=[]
for s in dict.fromkeys(cand):
    x=tk[s]; hi=float(x["high24Price"]); lo=float(x["lower24Price"]); last=float(x["lastPrice"]); f=float(x["fundingRate"])
    k=get(f"https://contract.mexc.com/api/v1/contract/kline/{s}?interval=Min60&start={int(now)-5*3600}")["data"]
    if len(k["close"])<3: continue
    o,h,l,c,t=k["open"][-2],k["high"][-2],k["low"][-2],k["close"][-2],k["time"][-2]; pl=k["low"][-3]
    rng=max(h-l,1e-12); up=(h-max(o,c))/rng
    seen.append(f"{s} {round(float(x['riseFallRate'])*100,1)}% last {last}")
    if h>=hi*0.97 and c<o and up>=0.4 and c<pl and now-st.get(s,0)>6*3600 and st.get(s+"_t")!=t:
        st[s]=now; st[s+"_t"]=t
        stop=h*1.02; risk=stop-c
        print(f"ALERT {s} 1h {time.strftime('%H:%M',time.gmtime(t+3600))} WAT o{o} h{h} c{c} | 24h +{round(float(x['riseFallRate'])*100,1)}% high {hi} low {lo} | funding {f} | live {last} | entry {c:.6g}-{(c+h)/2:.6g} stop {stop:.6g} tp1 {max(c-risk*1.5,lo):.6g} tp2 {max(c-risk*2.5,lo):.6g}")
    # Trigger 2: failed lower-high bounce (slow fade). High made >=2h ago, candle high 2-12% under it,
    # red close in lower 40% of range, and upper wick >=30% or close below prior low. Not >25% off the high already.
    try:
        k2=get(f"https://contract.mexc.com/api/v1/contract/kline/{s}?interval=Min60&start={int(now)-26*3600}")["data"]
        n=len(k2["close"])-1  # index of the open (live) candle; last closed is n-1
        if n>=4:
            hs=k2["high"][:n]; hi2=max(hs); hi_i=hs.index(hi2); j=n-1
            o2,h2,l2,c2,t2=k2["open"][j],k2["high"][j],k2["low"][j],k2["close"][j],k2["time"][j]; pl2=k2["low"][j-1]
            r2=max(h2-l2,1e-12); up2=(h2-max(o2,c2))/r2; pos=(c2-l2)/r2
            if (j-hi_i>=2 and hi2*0.88<=h2<=hi2*0.98 and c2<o2 and pos<=0.4 and (up2>=0.3 or c2<pl2)
                and c2>=hi2*0.75 and now-st.get(s+"_lh",0)>6*3600 and st.get(s+"_lht")!=t2):
                st[s+"_lh"]=now; st[s+"_lht"]=t2
                stop=h2*1.02; risk=stop-c2
                print(f"ALERT2 {s} 1h {time.strftime('%H:%M',time.gmtime(t2+3600))} WAT o{o2} h{h2} c{c2} | 24h +{round(float(x['riseFallRate'])*100,1)}% high {hi2} low {lo} | funding {f} | live {last} | entry {c2:.6g}-{(c2+h2)/2:.6g} stop {stop:.6g} tp1 {max(c2-risk*1.5,lo):.6g} tp2 {max(c2-risk*2.5,lo):.6g}")
    except Exception as e: print("lh err",s,e)
json.dump(st,open(S,"w"))
print("WATCH",", ".join(seen))
