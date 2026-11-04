# Generic auto-level watcher: python3 scripts/auto.py SYM (MEXC futures SYM_USDT, 15m). Levels follow price; see autolv.py.
import json,os,sys
sys.path.insert(0,"scripts"); import autolv
sym=sys.argv[1].upper(); ST=f"state/auto_{sym.lower()}.json"
s=json.load(open(ST)) if os.path.exists(ST) else {}
ks=autolv.run(sym,s)
json.dump(s,open(ST,"w"))
print("live",ks[-1][4])
