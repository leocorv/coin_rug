# coin_rug

This repository contains a simple example trading bot using the [ccxt](https://github.com/ccxt/ccxt) library.

## trade_bot.py

`trade_bot.py` connects to the Binance exchange and demonstrates a basic strategy for BTC/USDC, ETH/USDC and SOL/USDC. Each pair starts with an imaginary balance of 100 USDC.


The bot also tracks closing prices for each pair and sends periodic charts to a Discord webhook.

### Discord reporting

Every ten cycles, the bot generates a chart of closing prices for each pair and sends it to the provided Discord webhook.

### Strategy overview

1. Fetch historical OHLC data and compute technical indicators (EMA, RSI and Bollinger Bands).
2. If RSI is below 30, the close is above the EMA and below the lower Bollinger band, the bot buys using the available USDC balance.
3. After buying, the bot tracks the highest price reached. It sells either:
   - if the price drops 10% below the entry (stop loss)
   - or if the current price falls 10% from the highest price after entry (trailing stop)

API keys for Binance should be provided via the environment variables `BINANCE_API_KEY` and `BINANCE_API_SECRET`.
Set `DISCORD_WEBHOOK_URL` to receive periodic price charts for each coin on Discord.

You can store these variables in a `.env` file and install [python-dotenv](https://pypi.org/project/python-dotenv/) so the script loads them automatically:

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

This bot is an educational example and should not be used for real trading without further improvements and proper testing.
