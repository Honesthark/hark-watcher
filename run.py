# Hark Watcher: runs the alert scripts and sends Nox-style messages to Telegram.
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

TOKEN = os.environ.get("TG_TOKEN", "")
CHAT = os.environ.get("TG_CHAT", "")
DRY = "--dry" in sys.argv
if not DRY and not (TOKEN and CHAT): sys.exit("TG_TOKEN / TG_CHAT secret missing")
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


# ---- trade tracker: follow every signal sent until TP2, SL or 48h ----
TR = "state/trades.json"
trades = json.load(open(TR)) if os.path.exists(TR) else []


def num(pat, text):
    m = re.search(pat + r"\s*~?\s*([0-9]*\.?[0-9]+(?:e-?\d+)?)", text, re.I)
    return float(m.group(1)) if m else None


def track(sym, label, text, side="SHORT"):
    e, sl, t1, t2 = num(r"entry", text), num(r"(?:SL|stop)(?: above)?", text), num(r"TP1", text), num(r"TP2", text)
    if None in (e, sl, t1, t2): print("track skip", sym); return
    trades.append({"sym": sym, "label": label, "side": side, "entry": e, "sl": sl, "tp1": t1, "tp2": t2,
                   "t": time.time(), "chk": time.time(), "tp1hit": False})


def kl(sym, since):
    u = f"https://contract.mexc.com/api/v1/contract/kline/{sym}_USDT?interval=Min15&start={int(since)}"
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
    return list(zip(d["time"], d["high"], d["low"], d["close"]))


def check_trades():
    keep = []
    for tr in trades:
        try:
            ks = [k for k in kl(tr["sym"], tr["chk"] - 900) if k[0] + 900 > tr["chk"]]
        except Exception as ex:
            print("tracker", tr["sym"], ex); keep.append(tr); continue
        done = False; last = ks[-1][3] if ks else "?"
        d = -1 if tr.get("side", "SHORT") == "SHORT" else 1
        stop = tr["entry"] if tr["tp1hit"] else tr["sl"]
        pc = lambda v: abs(v - tr['entry']) / tr['entry'] * 100
        for _, h, l, c in ks:
            if (d == -1 and h >= stop) or (d == 1 and l <= stop):
                if tr["tp1hit"]:
                    send(f"➖ {tr['sym']} {tr['label']}: price came back to entry {tr['entry']} after TP1. Closed at breakeven on the rest, with TP1 profit kept. Live {last}")
                else:
                    send(f"❌ {tr['sym']} {tr['label']}: STOP HIT at {tr['sl']} (about -{pc(tr['sl']):.1f}% from entry {tr['entry']}, before leverage). Trade closed. Live {last}")
                done = True; break
            if not tr["tp1hit"] and ((d == -1 and l <= tr["tp1"]) or (d == 1 and h >= tr["tp1"])):
                tr["tp1hit"] = True; stop = tr["entry"]
                send(f"✅ {tr['sym']} {tr['label']}: TP1 HIT at {tr['tp1']} (+{pc(tr['tp1']):.1f}% from entry {tr['entry']}, before leverage). Consider taking partial profit and moving the stop to entry. Still tracking TP2 {tr['tp2']}. Live {last}")
            if tr["tp1hit"] and ((d == -1 and l <= tr["tp2"]) or (d == 1 and h >= tr["tp2"])):
                send(f"🎯 {tr['sym']} {tr['label']}: TP2 HIT at {tr['tp2']} (+{pc(tr['tp2']):.1f}% from entry {tr['entry']}, before leverage). Trade complete. Live {last}")
                done = True; break
        if ks: tr["chk"] = ks[-1][0]
        if not done and time.time() - tr["t"] > 48 * 3600:
            send(f"⌛ {tr['sym']} {tr['label']}: no TP2 or stop after 48h, so I've stopped tracking it. Live {last}"); done = True
        if not done: keep.append(tr)
    trades[:] = keep


check_trades()


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
            e0 = num(r"entry", plan); late = ""
            try:
                if e0 and float(live) < e0 * 0.98: late = " Price is already below entry, so wait for a bounce toward entry rather than chasing."
            except Exception: pass
            send(f"🔻 {sym} SHORT SIGNAL · {name}\n{cand}\nPlan: {plan}\nLive {live}.{late}\n{NOTE[sym]} Keep size small, 3-5x max. MEXC prices; Bybit may differ slightly. I'll ping you when TP or SL is hit.")
            track(sym, name, plan.replace("SL above", "SL"))
        elif ev == "ALERT BREAK":
            send(f"⚠️ {sym} HEADS-UP (not an entry yet)\n{body}\nLive {live}")
        elif ev == "MOMENTUM":
            if allow(sym + "MOM", 6): send(f"🟢 {sym} MOMENTUM, stay out\n{body}\nLive {live}")
        elif ev == "INVALID":
            send(f"↩️ {sym} setup B reset\n{body}\nLive {live}")

# ---- BTC & ETH trend-breakout signals (long and short) ----
for l in run(["python3", "scripts/majors.py"]).splitlines():
    m = re.match(r"SIGNAL (\w+) (LONG|SHORT) close (\S+) level (\S+) at (\S+) (.*) risk (\S+)", l)
    if not m: continue
    sym, side, cl, lvl, hhmm, plan, risk = m.groups()
    if any(t["sym"] == sym for t in trades): print("skip, open trade", sym); continue
    up = side == "LONG"
    why = (f"1h candle to {hhmm} WAT closed at {cl}, above the 24h high {lvl}, with the 1h trend up (EMA50 over EMA200)." if up else
           f"1h candle to {hhmm} WAT closed at {cl}, below the 24h low {lvl}, with the 1h trend down (EMA50 under EMA200).")
    p = dict(re.findall(r"(entry|SL|TP1|TP2) (\S+)", plan))
    send(f"{'🟢' if up else '🔻'} {sym} {side} SIGNAL · 24h {'breakout' if up else 'breakdown'}\n{why}\n"
         f"Entry ~{p['entry']} · SL {p['SL']} · TP1 {p['TP1']} · TP2 {p['TP2']}\n"
         f"Stop is {risk}% away, so at 10x a stop costs about {float(risk)*10:.0f}% of margin. Keep size small.\n"
         f"Backtest since Jun 2025: about 54% of these hit TP1 first; a thin edge, not a sure thing. MEXC prices. I'll ping you when TP or SL is hit.")
    track(sym, f"{side.lower()} breakout", plan, side)

# ---- gainers short watcher ----
for l in run(["python3", "scripts/gainers.py"]).splitlines():
    if not (l.startswith("ALERT ") or l.startswith("ALERT2 ")): continue
    lh = l.startswith("ALERT2")
    try:
        sym = l.split()[1].replace("_USDT", "")
        g = lambda k: re.search(k + r" ([\-0-9.e+]+)", l).group(1)
        t = re.search(r"1h (\d\d:\d\d) WAT", l).group(1)
        ch = re.search(r"24h \+([0-9.]+)%", l).group(1)
        fund = float(g("funding")) * 100; live = g("live"); tp1 = float(g("tp1"))
        entry = re.search(r"entry ([0-9.e\-]+-[0-9.e\-]+)", l).group(1)
        warn = " Funding is very negative, so shorts are crowded and squeeze risk is high." if fund < -0.1 else ""
        played = " Price is already past TP1, so the move has mostly played out. Don't chase it." if float(live) <= tp1 else ""
        why = (f"Lower-high bounce failed: the 1h candle to {t} WAT topped under the 24h high {g('high')} and closed weak at {g('c')}. Riskier than a top rejection, since the trend can resume." if lh else
               f"1h candle to {t} WAT tagged the 24h high {g('high')} and closed red at {g('c')}, below the prior hour's low.")
        send(f"🔻 SHORT SIGNAL{' (fade)' if lh else ''}: {sym} (+{ch}% 24h)\n{why} Funding {fund:+.3f}%.\n"
             f"Entry {entry} · SL {g('stop')} · TP1 {g('tp1')} · TP2 {g('tp2')}\nLive {live}.{played}{warn}\nUse 3-5x max and small size; these coins wick 20%+. MEXC prices." + ("" if played else " I'll ping you when TP or SL is hit."))
        if not played: track(sym, "fade short" if lh else "top short", f"entry {entry.split('-')[0]} SL {g('stop')} TP1 {g('tp1')} TP2 {g('tp2')}")
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
    tier = "🔴 MAJOR" if pct_mcap >= 5 else "🟠 LARGE" if pct_mcap >= 2 else "🔵 NOTABLE"
    icon = {"COLD TO HOT": "🔥", "HOT TO COLD": "🧊", "EXCHANGE DEPOSIT": "📥", "EXCHANGE WITHDRAWAL": "📤"}.get(j["kind"], "🐋")
    chain = "Ethereum" if j["chain"] == "ethereum" else "BNB Chain"
    send(f"{icon} {j['kind']}\n━━━━━━━━━━━━\n"
         f"📌 {j['sym']} · {chain}\n💰 ${j['usd']:,.0f} ({j['amount']:,.0f} tokens)\n"
         f"➡️ {sh(j['from'], j.get('from_label'))} → {sh(j['to'], j.get('to_label'))}\n\n"
         f"{tier}\n{pct_mcap:.2f}% of market cap · {pct_vol:.2f}% of daily volume\n\n"
         f"Market cap ${mc/1e6:.2f}M\nDaily volume (MEXC) ${(j.get('vol24_mexc_usd') or 0)/1e6:.2f}M\nPrice 24h {j.get('chg24', 0):+.2f}%\n\n"
         f"Derivatives (MEXC)\nOI ${oi/1e6:.2f}M ({oip:.0f}% of mcap)\nFunding {f:+.4f}%\n\n"
         f"Read\n> {READ.get(j['kind'], '')}\n> {pos}\n\n{FOOT}\n{txl}")

json.dump(rl, open(RL, "w"))
json.dump(trades, open(TR, "w"))
print("done")
