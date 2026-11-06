# One-off Telegram test: sample cards in the new % format (no margin/leverage). Run by .github/workflows/test.yml (manual).
import os, json, urllib.request, urllib.parse
T = os.environ["TG_TOKEN"]; C = os.environ.get("TG_CHAT") or "6335292530"
msgs = ["""🧪 TEST · new format (sample, not a live alert)

🔴 SHORT · NVIDIA
📌 Fixed setup, short
━━━━━━━━━━━━
🚪 Entry  189.6-190.0
🛑 Stop   191.3
🎯 TP1    188
🎯 TP2    186
💲 Now    189.40
📏 Stop −0.8% · TP1 +0.9% (price move)
━━━━━━━━━━━━
📊 15m candle closed at 189.4, below today's 190.0 low
🔔 I'll ping you at TP or stop.""",
"""🧪 TEST · new format (sample, not a live alert)

🎯 NVIDIA · TP2 HIT
Fixed setup, short
🟢 TP2 186 (+2.0% before leverage)
🏁 Trade complete
📈 +1.47% price move
⏱ Trade time: 1h 45m
📒 Today (half off at TP1): 1W-0L · +1.47% price move"""]
for msg in msgs:
    d = urllib.parse.urlencode({"chat_id": C, "text": msg}).encode()
    r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{T}/sendMessage", d, timeout=20))
    print("ok", r.get("ok"), "chat", str(r["result"]["chat"]["id"])[-3:])
