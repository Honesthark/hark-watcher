# Hark Watcher
Runs every 15 minutes on GitHub Actions and sends Telegram alerts:
- AIN, Q, BTW, IRYS short setups (fixed levels)
- MEXC top-gainer short triggers
- BTC and ETH 1h trend-breakout signals, long and short
- Whale / exchange transfers on-chain

Secrets needed: `TG_TOKEN` (Telegram bot token), `TG_CHAT` (chat ID).
Rule-based only: levels don't update themselves.
