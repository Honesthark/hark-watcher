# Breaking-news watcher (2026-11-07, user request). Reads Watcher Guru's public Telegram feed,
# keeps posts about NVDA, BTC/ETH, the user's coins, MEXC and big macro (Fed, CPI, jobs, tariffs).
# Prints: NEWS <tag>\t<id>\t<text>
import html, json, os, re, urllib.request
ST = "state/news.json"
SRC = ["WatcherGuru", "cryptocurrency_media"]   # cryptocurrency_media added 2026-11-07: early but noisy, so stricter filter + cap
NOISY = {"cryptocurrency_media": 4}   # max posts per run
PROMO = r"i use|referral|ref link|promo|giveaway|sign ?up|bonus|vpn|airdrop for|join (our|my)|subscribe|link in|we use|keyboard|sponsored|\bad\b"
NEWSY = r"just in|breaking|\b(says|said|reports?|announce[sd]?|approve[sd]?|ban(s|ned)?|files?|filed|launch(es|ed)?|buys?|bought|sells?|sold|dumps?|hack(ed)?|exploit|delist|suspend|halt|freez|froze|liquidat|cut|hike|raises?|rais|sanction|order(s|ed)?|sue[sd]?|charge[sd]?|arrest|close[sd]?|withdraw|outflow|inflow|etf)\b"
TAGS = [
    ("NVDA", r"\bnvidia\b|\$?NVDA\b|jensen huang|\bH20\b|\bH200\b|\bblackwell\b|chip (sales|export)"),
    ("BTC/ETH", r"\bbitcoin\b|\$?BTC\b|\bethereum\b|\$?ETH\b|\bether\b|spot etf|microstrategy|\bsaylor\b|\bblackrock\b"),
    ("EXCHANGE", r"\bMEXC\b|\bbinance\b|\bbybit\b|\bbitget\b|\bcoinbase\b|\bhack(ed)?\b|\bexploit|\bdelist"),
    ("COINS", r"\$(AIN|BTW|IRYS|EVAA|AKE|STRK|CLANKER|KOR|BIRB|UAI|TRUMP|HOT|ELSA)\b"),
    ("MACRO", r"\bfed\b|\bpowell\b|rate (cut|hike)|\bfomc\b|\bCPI\b|inflation|jobs report|nonfarm|unemployment|\btariff|recession|treasury|\bSEC\b"),
]
st = json.load(open(ST)) if os.path.exists(ST) else {}
out = []
seen = st.get("seen", [])[-40:]
found = {}
for ch in SRC:
    try:
        s = urllib.request.urlopen(urllib.request.Request(f"https://t.me/s/{ch}", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
    except Exception as e:
        print("news fetch fail", ch, e); continue
    posts = re.findall(r'data-post="' + ch + r'/(\d+)".*?<div class="tgme_widget_message_text[^>]*>(.*?)</div>', s, re.S)
    last = st.get(ch)
    for pid, raw in posts:
        pid = int(pid)
        if last is None or pid <= last: continue   # first run seeds silently
        txt = html.unescape(re.sub(r"<br\s*/?>", " ", raw)); txt = re.sub(r"<[^>]+>", "", txt)
        txt = re.sub(r"\s*@" + ch + r"\s*$", "", re.sub(r"\s+", " ", txt)).strip()
        tag = next((t for t, rx in TAGS if re.search(rx, txt, re.I)), None)
        if not tag: continue
        if ch in NOISY and (re.search(PROMO, txt, re.I) or not re.search(NEWSY, txt, re.I) or len(txt) < 35): continue
        key = set(re.findall(r"[a-z0-9$]{4,}", txt.lower()))
        if any(len(key & set(k)) >= 0.6 * max(1, min(len(key), len(k))) for k in seen): continue   # same story already sent from another channel
        seen.append(sorted(key)); found.setdefault(ch, []).append(f"NEWS {tag}\t{ch}/{pid}\t{txt[:400]}")
    if posts: st[ch] = max([int(p) for p, _ in posts] + [last or 0])
for ch in SRC: out += found.get(ch, [])[-NOISY.get(ch, 6):]

# ---- Jensen Huang probe headlines (Google News RSS, added 2026-11-10 at user request; replaces a Hark scheduled check). Expires after Nov 18 (post-earnings).
import time as _t
if _t.time() < 1795039200:
    GQ = "https://news.google.com/rss/search?q=%22Jensen+Huang%22+(investigation+OR+FBI+OR+probe+OR+board+OR+resign+OR+lawsuit+OR+Congress+OR+Commerce)&hl=en-US&gl=US&ceid=US:en"
    BIG = r"resign|step(s|ped)? down|steps aside|on leave|ouster|oust|replace|interim ceo|successor|fired|FBI|DOJ|Justice Department|\bSEC\b|subpoena|charge[sd]?|indict|arrest|congress|senate|house (panel|committee)|hearing|lawmakers|board (find|conclu|clear)|findings|cleared|export|commerce (dept|department)|lawsuit|sued|class action|megaspeed|earnings|guidance|delay"
    try:
        g = urllib.request.urlopen(urllib.request.Request(GQ, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode("utf-8", "ignore")
        items = re.findall(r"<item><title>(.*?)</title><link>(.*?)</link>", g)
        gs = st.get("gnews")
        new = []
        for t, l in items:
            t = html.unescape(t)
            k = re.sub(r"\s+-\s+[^-]+$", "", t).lower()[:90]
            if gs is not None and k not in gs and re.search(BIG, t, re.I):
                key = set(re.findall(r"[a-z0-9$]{4,}", t.lower()))
                if not any(len(key & set(x)) >= 0.6 * max(1, min(len(key), len(x))) for x in seen):
                    seen.append(sorted(key)); new.append(f"NEWS NVDA\t{html.unescape(l)}\t{t[:300]}")
        st["gnews"] = list(dict.fromkeys((gs or []) + [re.sub(r"\s+-\s+[^-]+$", "", html.unescape(t)).lower()[:90] for t, _ in items]))[-200:]
        out += new[:3]
    except Exception as e:
        print("gnews fail", e)
st["seen"] = seen[-40:]
json.dump(st, open(ST, "w"))
print("\n".join(out[-8:]))
