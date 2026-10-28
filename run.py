# Hark Watcher: runs the alert scripts and sends Nox-style messages to Telegram.
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

TOKEN = os.environ.get("TG_TOKEN", "")
CHAT = os.environ.get("TG_CHAT", "")
DRY = "--dry" in sys.argv
RL = "state/ratelimit.json"
rl = json.load(open(RL)) if os.path.exists(RL) else {}
FOOT = "Not a trade signal on its own. Keep size small, 3-5x max. MEXC data; Bybit may differ."
NOTE = {"AIN": "AIN wicks 15-20% in an hour.", "Q": "Q is a low-cap pump coin with huge wicks.",
        "BTW": "BTW has a thin book and huge wicks.", "IRYS": "IRYS has very thin books and huge wicks."}


def send(text):
    if DRY or not TOKEN:
        print("---\n" + text); return
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text, "disable_web_page_preview": "true"}).encode()
    for _ in range(2):
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data, timeout=20); return
        except Exception as e:
            print("send failed", e); time.sleep(3)


def run(cmd):
    for _ in range(2):
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        if p.returncode == 0: return p.stdout
        print(cmd, "failed:", p.stderr[-400:]); time.sleep(5)
    return ""


def allow(key, hours):
    now = time.time()
    if now - rl.get(key, 0) < hours * 3600: return False
    rl[key] = now; return True


def fmt(n):
    n = float(n)
    return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.1f}k" if n >= 1e3 else f"{n:.0f}"


# ---- setup watchers ----
for sym, script in [("AIN", "ain"), ("Q", "qusdt"), ("BTW", "btw"), ("IRYS", "irys")]:
    out = run(["python3", f"scripts/{script}.py"])
    live = next((l.split()[1] for l in out.splitlines() if l.startswith("live ")), "?")
    for l in out.splitlines():
        if l.startswith("live"): continue
        m = re.match(r"(ALERT [A-Z ]+|MOMENTUM|INVALID):\s*(.*)", l)
        if not m: continue
        ev, body = m.group(1), m.group(2)
        if ev in ("ALERT REJECTION", "ALERT RETEST FAILED", "ALERT SETUP A", "ALERT SETUP B"):
            name = {"ALERT REJECTION": "Setup A, bounce rejected", "ALERT SETUP A": "Setup A, top failed",
                    "ALERT SETUP B": "Setup B, blow-off rejected", "ALERT RETEST FAILED": "Setup B, failed retest"}[ev]
            if sym in ("Q", "AIN") and ev in ("ALERT REJECTION", "ALERT SETUP A") and not allow(sym + ev, 3 if sym == "AIN" else 2): continue
            cand, plan = (body.split(" Short plan: ") + [""])[:2]
            send(f"🔻 {sym} SHORT SIGNAL · {name}\n{cand}\nPlan: {plan}\nLive {live}\n{NOTE[sym]} Keep size small, 3-5x max. MEXC prices; Bybit may differ slightly.")
        elif ev == "ALERT BREAK":
            send(f"⚠️ {sym} HEADS-UP (not an entry yet)\n{body}\nLive {live}")
        elif ev == "MOMENTUM":
            if allow(sym + "MOM", 6): send(f"🟢 {sym} MOMENTUM, stay out\n{body}\nLive {live}")
        elif ev == "INVALID":
            send(f"↩️ {sym} setup B reset\n{body}\nLive {live}")

# ---- gainers short watcher ----
for l in run(["python3", "scripts/gainers.py"]).splitlines():
    if not l.startswith("ALERT "): continue
    try:
        sym = l.split()[1].replace("_USDT", "")
        g = lambda k: re.search(k + r" ([\-0-9.e+]+)", l).group(1)
        t = re.search(r"1h (\d\d:\d\d) WAT", l).group(1)
        ch = re.search(r"24h \+([0-9.]+)%", l).group(1)
        fund = float(g("funding")) * 100; live = g("live"); tp1 = float(g("tp1"))
        entry = re.search(r"entry ([0-9.e\-]+-[0-9.e\-]+)", l).group(1)
        warn = " Funding is very negative, so shorts are crowded and squeeze risk is high." if fund < -0.1 else ""
        played = " Price is already past TP1, so the move has mostly played out. Don't chase it." if float(live) <= tp1 else ""
        send(f"🔻 SHORT SIGNAL: {sym} (+{ch}% 24h)\n1h candle to {t} WAT tagged the 24h high {g('high')} and closed red at {g('c')}, below the prior hour's low. Funding {fund:+.3f}%.\n"
             f"Entry {entry} · SL {g('stop')} · TP1 {g('tp1')} · TP2 {g('tp2')}\nLive {live}.{played}{warn}\nUse 3-5x max and small size; these coins wick 20%+. MEXC prices.")
    except Exception as e:
        print("gainer parse", e, l)

# ---- on-chain whale alerts ----
moves = {}
for l in run(["node", "scripts/onchain.mjs"]).splitlines():
    try: j = json.loads(l)
    except Exception: continue
    if "kind" not in j or j["kind"] in ("MINT", "BURN"): continue
    lbl = (j.get("from_label") or "") + (j.get("to_label") or "")
    if any(w in lbl.lower() for w in ("router", "pancake", "pool", "uniswap")) and (j.get("pct_mcap") or 0) < 2: continue
    k = (j["sym"], j["from"], j["to"])
    if k in moves: moves[k]["amount"] += j["amount"]; moves[k]["usd"] += j["usd"]; moves[k]["txs"].append(j["tx"])
    else: j["txs"] = [j["tx"]]; moves[k] = j
READ = {"COLD TO HOT": "Exchange housekeeping, not confirmed selling. It does stage inventory, so watch for follow-on moves.",
        "HOT TO COLD": "Exchange housekeeping; coins moving to storage.",
        "INTERNAL EXCHANGE": "Internal exchange shuffle, not confirmed selling.",
        "EXCHANGE DEPOSIT": "A private wallet sending to an exchange is possible sell pressure, not confirmed.",
        "EXCHANGE WITHDRAWAL": "Withdrawal to a private wallet is neutral to mildly bullish.",
        "EXCHANGE TO EXCHANGE": "Exchange-to-exchange move; often market-maker or rebalancing.",
        "WHALE TRANSFER": "Unlabeled to unlabeled, so the intent is unclear."}
sh = lambda a, lab: lab or (a[:6] + "…" + a[-4:])
for j in moves.values():
    mc = j.get("mcap") or 0; oi = j.get("oi_usd_mexc") or 0; f = (j.get("funding") or 0) * 100
    oip = oi / mc * 100 if mc else 0
    pos = ("Negative funding with OI above 50% of mcap means crowded shorts and squeeze risk." if f < 0 and oip > 50 else
           "Hot positive funding: longs are crowded, so dump risk is up." if f >= 0.1 else
           "Funding is mildly positive, so longs pay a little. OI isn't extreme." if f > 0 else
           "Funding is slightly negative. OI isn't extreme." if oip <= 50 else "OI is high relative to mcap.")
    pct_mcap = j.get("pct_mcap") or (j["usd"] / mc * 100 if mc else 0)
    pct_vol = j.get("pct_vol") or 0
    scan = "https://etherscan.io/tx/" if j["chain"] == "ethereum" else "https://bscscan.com/tx/"
    txl = "\n".join(scan + t for t in j["txs"][:3])
    send(f"🚨 {j['sym']} {j['kind']} · {fmt(j['amount'])} {j['sym']} (~${j['usd']:,.0f}) · {pct_mcap:.2f}% of mcap, {pct_vol:.2f}% of 24h vol\n"
         f"From {sh(j['from'], j.get('from_label'))} → {sh(j['to'], j.get('to_label'))}\n"
         f"Mcap ${mc/1e6:.1f}M · 24h {j.get('chg24', 0):+.2f}% · MEXC OI ${oi/1e6:.2f}M ({oip:.0f}% of mcap) · funding {f:+.3f}%\n"
         f"Read: {READ.get(j['kind'], '')} {pos}\n{FOOT}\n{txl}")

json.dump(rl, open(RL, "w"))
print("done")
