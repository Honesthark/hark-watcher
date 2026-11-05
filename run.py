# Hark Watcher: runs the alert scripts and sends Nox-style messages to Telegram.
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

TOKEN = os.environ.get("TG_TOKEN", "")
CHAT = "6335292530"  # @Bbyboss22 private chat with @Harkwatch_bot
_ENVCHAT = os.environ.get("TG_CHAT", "")
DRY = "--dry" in sys.argv
if not DRY and not (TOKEN and CHAT): sys.exit("TG_TOKEN / TG_CHAT secret missing")
RL = "state/ratelimit.json"
rl = json.load(open(RL)) if os.path.exists(RL) else {}
FOOT = "Not a trade signal on its own. Keep size small, 3-5x max. MEXC data; Bybit may differ."
NOTE = {"AIN": "AIN wicks 15-20% in an hour.", "Q": "Q is a low-cap pump coin with huge wicks.",
        "BTW": "BTW has a thin book and huge wicks.", "IRYS": "IRYS has very thin books and huge wicks.",
        "EVAA": "EVAA just wicked +23% in one hour, so stops can get run.",
        "STRK": "STRK has a big unlock around Nov 13-15 and 30M just hit Bybit, but rallies on news can be sharp.",
        "AKE": "AKE is deeply oversold after a -31% day, and relief bounces can be sharp, so stops get run.",
        "CLANKER": "CLANKER ran +35% in a day, so swings and squeezes are violent.",
        "KOR": "KOR is a fresh listing down ~70% with a thin book, so wicks of 20% happen."}


def send(text):
    if DRY or not TOKEN:
        print("---\n" + text); return
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text, "disable_web_page_preview": "true"}).encode()
    for _ in range(2):
        try:
            r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data, timeout=20))
            print("sent ok", r.get("ok"), "bot", r["result"]["from"].get("username"), "chat", str(r["result"]["chat"]["id"])[-3:], "envchat", _ENVCHAT[-3:]); return
        except Exception as e:
            print("send failed", e); time.sleep(3)


def run(cmd, timeout=150, tries=2):
    for _ in range(tries):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            print(cmd, "timed out"); out = e.stdout or ""
            return out.decode() if isinstance(out, bytes) else out
        if p.returncode == 0: return p.stdout
        print(cmd, "failed:", p.stderr[-400:]); time.sleep(5)
    return ""


def allow(key, hours):
    now = time.time()
    if now - rl.get(key, 0) < hours * 3600: return False
    rl[key] = now; return True


LINE = "━━━━━━━━━━━━"


def card(head, sub, rows, why="", risk="", tail=""):
    w = max(len(k) for k, _ in rows) if rows else 0
    out = [head] + ([sub] if sub else []) + [LINE]
    out += [f"{k.ljust(w)}  {v}" for k, v in rows]
    out.append(LINE)
    if why: out.append(f"📊 {why}")
    if risk: out.append(f"❗️ {risk}")
    if tail: out.append(tail)
    return "\n".join(out)


def bar(p):
    n = max(0, min(10, round(p / 10)))
    return "▰" * n + "▱" * (10 - n)


def board(sym, rows):
    out = [f"📋 {sym} WHALE BOARD · {len(rows)} wallets", LINE]
    ts = tn = 0; sellers = 0
    for i, (w, st, nw) in enumerate(rows, 1):
        ts += st; tn += nw; short = f"{w[:6]}…{w[-4:]}"
        if st <= 0:
            out.append(f"⚪ {i} · {short} · empty"); continue
        sold = st - nw; kept = nw / st * 100
        if sold > 1e6:
            sellers += 1
            out.append(f"🔴 {i} · {short}\n     {fmt(nw)} ({nw/1e9:.2f}%) · sold {fmt(sold)}\n     {bar(kept)} {kept:.0f}% left")
        else:
            out.append(f"🟢 {i} · {short} · {fmt(nw)} ({nw/1e9:.2f}%) · 100%")
    out += [LINE, f"🔴 Sold: {sellers} of {len(rows)} · 🟢 Holding: {sum(1 for _, st, nw in rows if st > 0 and st - nw <= 1e6)}",
            f"📦 Left: {tn/1e9:.2f}B ({tn/1e9:.2f}% supply) · kept {tn/ts*100:.1f}%", f"💸 Sold so far: {fmt(ts - tn)}"]
    return "\n".join(out)


def raw(pat, text):
    m = re.search(pat + r"\s*~?\s*([0-9]*\.?[0-9]+(?:\s*-\s*[0-9]*\.?[0-9]+)?)", text, re.I)
    return m.group(1).replace(" ", "") if m else "?"


def fmt(n):
    n = float(n)
    return f"{n/1e9:.2f}B" if n >= 1e9 else f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.1f}k" if n >= 1e3 else f"{n:.0f}"


# ---- trade tracker: follow every signal sent until TP2, SL or 48h ----
TR = "state/trades.json"
trades = json.load(open(TR)) if os.path.exists(TR) else []


def num(pat, text):
    m = re.search(pat + r"\s*~?\s*([0-9]*\.?[0-9]+(?:e-?\d+)?)", text, re.I)
    return float(m.group(1)) if m else None


def track(sym, label, text, side="SHORT"):
    e, sl, t1, t2 = num(r"entry", text), num(r"(?:SL|stop)(?: above)?", text), num(r"TP1", text), num(r"TP2", text)
    if None in (e, sl, t1, t2): print("track skip", sym); return
    if any(t["sym"] == sym and t["label"] == label and t["entry"] == e for t in trades): print("already tracking", sym); return
    trades.append({"sym": sym, "label": label, "side": side, "entry": e, "sl": sl, "tp1": t1, "tp2": t2,
                   "t": time.time(), "chk": time.time(), "tp1hit": False})


def kl(sym, since):
    u = f"https://contract.mexc.com/api/v1/contract/kline/{sym}_USDT?interval=Min5&start={int(since)}"
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "curl/8.5.0"}), timeout=20))["data"]
    return list(zip(d["time"], d["high"], d["low"], d["close"]))


def check_trades():
    keep = []
    for tr in trades:
        try:
            ks = [k for k in kl(tr["sym"], tr["chk"] - 300) if k[0] + 300 > tr["chk"]]
        except Exception as ex:
            print("tracker", tr["sym"], ex); keep.append(tr); continue
        done = False; last = ks[-1][3] if ks else "?"
        d = -1 if tr.get("side", "SHORT") == "SHORT" else 1
        stop = tr["entry"] if tr["tp1hit"] else tr["sl"]
        pc = lambda v: abs(v - tr['entry']) / tr['entry'] * 100
        def dur(ts):
            m = max(1, int((min(time.time(), ts + 300) - tr["t"]) // 60))
            return f"{m} mins" if m < 60 else f"{m // 60}h {m % 60}m"
        for ts, h, l, c in ks:
            if (d == -1 and h >= stop) or (d == 1 and l <= stop):
                if tr["tp1hit"]:
                    send(f"➖ {tr['sym']} · BREAKEVEN\n{tr['label']}\nBack to entry {tr['entry']} after TP1\n✅ TP1 profit kept · trade closed\n💲 Now {last}\n⏱ Trade time: {dur(ts)}")
                else:
                    send(f"❌ {tr['sym']} · STOP HIT\n{tr['label']}\n🔴 Stop {tr['sl']} (−{pc(tr['sl']):.1f}% before leverage)\nEntry was {tr['entry']} · trade closed\n💲 Now {last}\n⏱ Trade time: {dur(ts)}")
                done = True; break
            if not tr["tp1hit"] and ((d == -1 and l <= tr["tp1"]) or (d == 1 and h >= tr["tp1"])):
                tr["tp1hit"] = True; stop = tr["entry"]
                send(f"✅ {tr['sym']} · TP1 HIT\n{tr['label']}\n🟢 TP1 {tr['tp1']} (+{pc(tr['tp1']):.1f}% before leverage)\n👉 Take partial profit, move stop to entry {tr['entry']}\n🎯 Next: TP2 {tr['tp2']}\n💲 Now {last}\n⏱ Trade time: {dur(ts)}")
            if tr["tp1hit"] and ((d == -1 and l <= tr["tp2"]) or (d == 1 and h >= tr["tp2"])):
                send(f"🎯 {tr['sym']} · TP2 HIT\n{tr['label']}\n🟢 TP2 {tr['tp2']} (+{pc(tr['tp2']):.1f}% before leverage)\n🏁 Trade complete\n💲 Now {last}\n⏱ Trade time: {dur(ts)}")
                done = True; break
        if ks: tr["chk"] = ks[-1][0]
        if not done and time.time() - tr["t"] > 48 * 3600:
            send(f"⌛ {tr['sym']} · EXPIRED\n{tr['label']}\nNo TP2 or stop in 48h · stopped tracking\n💲 Now {last}"); done = True
        if not done: keep.append(tr)
    trades[:] = keep


OB = "state/outbox.json"
if os.path.exists(OB):
    for m in json.load(open(OB)): send(m)
    os.remove(OB)

check_trades()


# ---- setup watchers ----
# All setup levels follow price (scripts/autolv.py, 2026-11-04). auto.py SYM = levels only; ake/btw/strk add their extras.
WATCH = [("AIN", "scripts/auto.py AIN"), ("Q", "scripts/auto.py Q"), ("BTW", "scripts/btw.py"), ("IRYS", "scripts/auto.py IRYS"),
         ("EVAA", "scripts/auto.py EVAA"), ("AKE", "scripts/ake.py"), ("STRK", "scripts/strk.py"), ("CLANKER", "scripts/auto.py CLANKER"), ("KOR", "scripts/auto.py KOR")]
def setups():
    for sym, script in WATCH:
        out = run(["python3"] + script.split())
        live = next((l.split()[1] for l in out.splitlines() if l.startswith("live ")), "?")
        whale = []
        for l in out.splitlines():
            if l.startswith("BOARD ") and whale:
                whale[-1] += "\n\n" + board(sym, json.loads(l[6:])); continue
            if l.startswith("live") or l.startswith("BOARD "): continue
            if l.startswith("WHALE "):
                parts = l.split(); _, kind, w, amt, left, usd, tot = parts[:7]
                chg, fr, st0 = (parts[7:10] + ["na", "na", "0"])[:3]
                sell = kind == "SELL"; st0 = float(st0)
                pct = float(left) / st0 * 100 if st0 > 0 else None
                top = f"{'🔴 SOLD' if sell else ('🟢 RECEIVED' if sym == 'STRK' else '🟢 BOUGHT')} {fmt(amt)} ${sym} · ~${float(usd):,.0f}"
                if pct is not None: top += f"\n{bar(pct)} {pct:.0f}% of their starting {sym} left"
                whale.append(top + "\n\n" + card(f"🐋 {sym} · WHALE {kind} {'🔴' if sell else '🟢'}", f"{w[:6]}…{w[-4:]}",
                          [("💰 Moved", f"{fmt(amt)} {sym} (~${float(usd):,.0f})"), ("👛 Left", fmt(left) + (f" ({pct:.0f}% of start)" if pct is not None else "")),
                           *([("📦 13 wallets", f"{float(tot)/1e9:.2f}B ({float(tot)/1e9:.1f}% supply)")] if sym == "AKE" else []), ("💲 Now", live),
                           ("📈 24h", f"{chg}%"), ("💸 Funding", f"{fr}%" + (" 🔥 crowded shorts" if fr != "na" and float(fr) < -0.1 else ""))],
                          risk="More supply can hit the market. Watch the short setups." if sell else ("Wallet refilled: it sent 30M to Bybit on Nov 4, so another deposit may follow." if sym == "STRK" else ""),
                          tail=f"🔗 https://{'etherscan.io' if sym == 'STRK' else 'bscscan.com'}/address/{w}"))
                continue
            m = re.match(r"(ALERT [A-Z ]+|MOMENTUM|INVALID):\s*(.*)", l)
            if not m: continue
            ev, body = m.group(1), m.group(2)
            if ev in ("ALERT REJECTION", "ALERT RETEST FAILED", "ALERT SETUP A", "ALERT SETUP B", "ALERT BREAKDOWN"):
                name = {"ALERT REJECTION": "Auto, rejected at 4h high", "ALERT SETUP A": "Setup A, top failed",
                        "ALERT SETUP B": "Setup B, blow-off rejected", "ALERT RETEST FAILED": "Setup B, failed retest", "ALERT BREAKDOWN": "Setup B, 1h breakdown"}[ev]
                if sym in ("Q", "AIN", "STRK") and ev in ("ALERT REJECTION", "ALERT SETUP A") and not allow(sym + ev, 2 if sym == "Q" else 3): continue
                cand, plan = (body.split(" Short plan: ") + [""])[:2]
                e0 = num(r"entry", plan); late = ""
                if any(t["sym"] == sym and t["label"] == name and t["entry"] == e0 for t in trades): print("dup signal", sym); continue
                try:
                    if e0 and float(live) < e0 * 0.98: late = " Price is already below entry, so wait for a bounce toward entry rather than chasing."
                except Exception: pass
                why = re.sub(r"\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d\d:\d\d-\d\d:\d\d WAT", "", cand).strip().rstrip(".")
                send(card(f"🔴 SHORT · {sym}", f"📌 {name}",
                          [("🚪 Entry", raw(r"entry", plan)), ("🛑 Stop", raw(r"SL(?: above)?", plan)),
                           ("🎯 TP1", raw(r"TP1", plan)), ("🎯 TP2", raw(r"TP2", plan)), ("💲 Now", live)],
                          why, f"{NOTE[sym]} 3-5x max, small size." + (" Price is below entry, wait for a bounce. Don't chase." if late else ""),
                          "🔔 I'll ping you at TP or stop."))
                track(sym, name, plan.replace("SL above", "SL"))
            elif ev == "ALERT LONG DIP":
                name = "Auto, bounced off 4h low"
                if not allow(sym + ev, 2): continue
                cand, plan = (body.split(" Long plan: ") + [""])[:2]
                e0 = num(r"entry", plan); late = False
                if any(t["sym"] == sym and t["label"] == name for t in trades): print("dup long", sym); continue
                try: late = bool(e0 and float(live) > e0 * 1.02)
                except Exception: pass
                why = re.sub(r"\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d\d:\d\d-\d\d:\d\d WAT", "", cand).strip().rstrip(".")
                send(card(f"🟢 LONG · {sym}", f"📌 {name}",
                          [("🚪 Entry", raw(r"entry", plan)), ("🛑 Stop", raw(r"SL(?: below)?", plan)),
                           ("🎯 TP1", raw(r"TP1", plan)), ("🎯 TP2", raw(r"TP2", plan)), ("💲 Now", live)],
                          why, f"{NOTE[sym]} 3x max, small size." + (" Price already bounced above entry, wait for a dip. Don't chase." if late else ""),
                          "🔔 I'll ping you at TP or stop."))
                track(sym, name, plan.replace("SL below", "SL"), "LONG")
            elif ev == "ALERT BREAK":
                send(f"⚠️ {sym} · HEADS-UP\nNot an entry yet\n{LINE}\n📊 {body}\n💲 Now {live}")
            elif ev == "MOMENTUM":
                if allow(sym + "MOM", 6): send(f"🟢 {sym} · MOMENTUM UP\n⛔ Shorts invalid, stay out\n{LINE}\n📊 {body}\n💲 Now {live}")
            elif ev == "INVALID":
                send(f"↩️ {sym} · SETUP B RESET\n{LINE}\n📊 {body}\n💲 Now {live}")

        for m_ in whale: send(m_)

setups()

# ---- BTC & ETH trend-breakout signals (long and short) ----
def handle_signals(out):
  for l in out.splitlines():
      m = re.match(r"SIGNAL (\w+) (LONG|SHORT) close (\S+) level (\S+) at (\S+) (.*) risk (\S+)", l)
      if not m: continue
      sym, side, cl, lvl, hhmm, plan, risk = m.groups()
      if any(t["sym"] == sym for t in trades): print("skip, open trade", sym); continue
      up = side == "LONG"
      rk = re.search(r"kind rsi(\d*) (\d+)", l); m15 = bool(rk and rk.group(1))
      why = (f"1h close {cl} broke above the 24h high {lvl}, trend up" if up else f"1h close {cl} broke below the 24h low {lvl}, trend down")
      if rk: why = (f"{'15m ' if m15 else '1h '}RSI {rk.group(2)}: oversold dip inside an uptrend, snap-back long" if up else f"{'15m ' if m15 else '1h '}RSI {rk.group(2)}: overbought pop inside a downtrend, snap-back short")
      p = dict(re.findall(r"(entry|SL|TP1|TP2) (\S+)", plan))
      send(card(f"{'🟢 LONG' if up else '🔴 SHORT'} · {sym}", (f"📌 {'15m' if m15 else '1h'} RSI snap-back · {hhmm} WAT" if rk else f"📌 24h {'breakout' if up else 'breakdown'} · {hhmm} WAT"),
                [("🚪 Entry", p['entry']), ("🛑 Stop", f"{p['SL']} ({risk}%)"), ("🎯 TP1", p['TP1']), ("🎯 TP2", p['TP2'])],
                why, f"At 10x a stop costs ~{float(risk)*10:.0f}% of margin. " + ("Backtest 71% hit TP1 first (~14/month). Close most at TP1; stop is 1.5x TP1." if m15 else "Backtest 72% hit TP1 first. Close most at TP1; the stop is 2x wider than TP1." if rk else "NVDA backtest ~50% hit TP1 first, about breakeven: use your levels." if sym == "NVIDIA" else "Backtest ~54% hit TP1 first."),
                "🔔 I'll ping you at TP or stop."))
      track(sym, f"{side.lower()} {'rsi snap-back' if rk else 'breakout'}", plan, side)

handle_signals(run(["python3", "scripts/majors.py"]))
handle_signals(run(["python3", "scripts/nvda15.py"]))

# ---- gainers short watcher ----
for l in run(["python3", "scripts/gainers.py"]).splitlines():
    if not (l.startswith("ALERT ") or l.startswith("ALERT2 ")): continue
    lh = l.startswith("ALERT2")
    try:
        sym = l.split()[1].replace("_USDT", "")
        g = lambda k: re.search(r"(?:^|[ |])" + k + r" ?([\-0-9.e+]+)", l).group(1)
        t = re.search(r"1h (\d\d:\d\d) WAT", l).group(1)
        ch = re.search(r"24h \+([0-9.]+)%", l).group(1)
        fund = float(g("funding")) * 100; live = g("live"); tp1 = float(g("tp1"))
        entry = re.search(r"entry ([0-9.e\-]+-[0-9.e\-]+)", l).group(1)
        warn = " Funding very negative: squeeze risk." if fund < -0.1 else ""
        played = float(live) <= tp1
        why = (f"Lower-high bounce failed under 24h high {g('high')}, closed {g('c')}. Riskier, trend can resume" if lh else
               f"Tagged 24h high {g('high')} and closed red at {g('c')}")
        send(card(f"🔴 SHORT{' (fade)' if lh else ''} · {sym}", f"📌 +{ch}% in 24h · {t} WAT",
                  [("🚪 Entry", entry), ("🛑 Stop", g('stop')), ("🎯 TP1", g('tp1')), ("🎯 TP2", g('tp2')),
                   ("💲 Now", live), ("💸 Funding", f"{fund:+.3f}%")],
                  why, "Wicks 20%+. 3-5x max, small size." + warn,
                  "⛔ Already past TP1, don't chase." if played else "🔔 I'll ping you at TP or stop."))
        if not played: track(sym, "fade short" if lh else "top short", f"entry {entry.split('-')[0]} SL {g('stop')} TP1 {g('tp1')} TP2 {g('tp2')}")
    except Exception as e:
        print("gainer parse", e, l)

# ---- on-chain whale alerts ----
moves = {}
for l in run(["node", "scripts/onchain.mjs"], 120, 1).splitlines():
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
    send(card(f"{icon} {j['sym']} · {j['kind']}", f"{tier} · {chain}",
              [("💰 Size", f"${j['usd']:,.0f} ({fmt(j['amount'])})"), ("➡️ Route", f"{sh(j['from'], j.get('from_label'))} → {sh(j['to'], j.get('to_label'))}"),
               ("📊 Mcap", f"{pct_mcap:.2f}% of ${mc/1e6:.1f}M"), ("📈 24h", f"{j.get('chg24', 0):+.2f}%"),
               ("💸 Funding", f"{f:+.4f}%"), ("📂 OI", f"{oip:.0f}% of mcap")],
              READ.get(j['kind'], ''), pos, "🔗 " + txl))

json.dump(rl, open(RL, "w"))
json.dump(trades, open(TR, "w"))

# ---- fast tracker loop: GitHub cron fires about hourly, so keep checking stops/TPs every minute ----
if not DRY:
    end = time.time() + 50 * 60
    last_setup = time.time()
    while time.time() < end:
        time.sleep(60)
        handle_signals(run(["python3", "scripts/nvda15.py"], 60, 1))
        if time.time() // 900 != last_setup // 900 and time.time() % 900 > 45:  # once per 15m candle, just after it closes
            last_setup = time.time()
            try: setups()
            except Exception as e: print("setups err", e)
        check_trades()
        json.dump(trades, open(TR, "w"))
print("done")
