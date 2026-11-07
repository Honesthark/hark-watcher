# Breaking-news watcher (2026-11-07, user request). Reads Watcher Guru's public Telegram feed,
# keeps posts about NVDA, BTC/ETH, the user's coins, MEXC and big macro (Fed, CPI, jobs, tariffs).
# Prints: NEWS <tag>\t<id>\t<text>
import html, json, os, re, urllib.request
ST = "state/news.json"
SRC = ["WatcherGuru"]
TAGS = [
    ("NVDA", r"\bnvidia\b|\$?NVDA\b|jensen huang|\bH20\b|\bH200\b|\bblackwell\b|chip (sales|export)"),
    ("BTC/ETH", r"\bbitcoin\b|\$?BTC\b|\bethereum\b|\$?ETH\b|\bether\b|spot etf|microstrategy|\bsaylor\b|\bblackrock\b"),
    ("EXCHANGE", r"\bMEXC\b|\bbinance\b|\bbybit\b|\bbitget\b|\bcoinbase\b|\bhack(ed)?\b|\bexploit|\bdelist"),
    ("COINS", r"\$(AIN|BTW|IRYS|EVAA|AKE|STRK|CLANKER|KOR|BIRB|UAI|TRUMP|HOT|ELSA)\b"),
    ("MACRO", r"\bfed\b|\bpowell\b|rate (cut|hike)|\bfomc\b|\bCPI\b|inflation|jobs report|nonfarm|unemployment|\btariff|recession|treasury|\bSEC\b"),
]
st = json.load(open(ST)) if os.path.exists(ST) else {}
out = []
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
        if tag: out.append(f"NEWS {tag}\t{pid}\t{txt}")
    if posts: st[ch] = max([int(p) for p, _ in posts] + [last or 0])
json.dump(st, open(ST, "w"))
print("\n".join(out[-6:]))
