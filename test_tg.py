# One-off Telegram test: sends a sample AKE whale alert in the new format. Run by .github/workflows/test.yml (manual).
import os, json, urllib.request, urllib.parse
T = os.environ["TG_TOKEN"]; C = os.environ.get("TG_CHAT") or "6335292530"
msg = """🧪 TEST · Hark Watcher

🔴 SOLD 206.30M $AKE · ~$635
▰▰▰▰▰▰▰▱▱▱ 74% of their starting AKE left

🐋 AKE · WHALE SELL 🔴
0xaf6b…9da1
━━━━━━━━━━━━
💰 Moved  206.30M AKE (~$635)
👛 Left   1.71B (74% of start)
━━━━━━━━━━━━
📋 AKE WHALE BOARD
🔴 1 · 0x76e3…015F
     903.89M · sold 168.58M
     ▰▰▰▰▰▰▰▰▱▱ 84% left
🔴 2 · 0xaf6b…9da1
     1.71B · sold 607.34M
     ▰▰▰▰▰▰▰▱▱▱ 74% left

(Sample only, built from this morning's balances. Not a live alert.)"""
d = urllib.parse.urlencode({"chat_id": C, "text": msg}).encode()
r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{T}/sendMessage", d, timeout=20))
print("ok", r.get("ok"), "chat", str(r["result"]["chat"]["id"])[-3:])
