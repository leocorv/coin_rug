import os
import time
from typing import Dict, List
import ccxt
import pandas as pd
import ta
import matplotlib.pyplot as plt
import requests
from io import BytesIO


class Trader:
    def __init__(self, api_key: str, api_secret: str, webhook_url: str, base_currency: str = 'USDC'):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        self.base_currency = base_currency
        self.webhook_url = webhook_url
        # Start with 100 USDC for each coin
        self.balances: Dict[str, float] = {
            f'BTC/{base_currency}': 100.0,
            f'ETH/{base_currency}': 100.0,
            f'SOL/{base_currency}': 100.0,
        }
        self.positions: Dict[str, Dict[str, float]] = {}
        self.price_history: Dict[str, List[float]] = {symbol: [] for symbol in self.balances.keys()}
        self.tick = 0

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """Fetch historical OHLCV data."""
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def calculate_indicators(self, df: pd.DataFrame):
        """Calculate RSI, EMA and Bollinger Bands."""
        df['ema'] = ta.trend.ema_indicator(df['close'], window=20)
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        return df

    def should_buy(self, df: pd.DataFrame) -> bool:
        """Simple buy condition based on RSI and close price vs EMA."""
        latest = df.iloc[-1]
        return (
            latest['rsi'] < 30 and
            latest['close'] > latest['ema'] and
            latest['close'] < latest['bb_low']
        )

    def send_chart(self, symbol: str):
        """Plot price history and send it to Discord."""
        prices = self.price_history.get(symbol)
        if not prices or not self.webhook_url:
            return
        plt.figure()
        plt.plot(prices)
        plt.title(symbol)
        plt.xlabel('Tick')
        plt.ylabel('Close Price')
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        files = {'file': ('chart.png', buf, 'image/png')}
        try:
            requests.post(self.webhook_url, files=files, timeout=10)
        except Exception as e:
            print(f"Error sending chart to Discord: {e}")

    def run(self):
        symbols = list(self.balances.keys())
        while True:
            self.tick += 1
            for symbol in symbols:
                try:
                    data = self.fetch_ohlcv(symbol)
                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
                    continue

                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df = self.calculate_indicators(df)

                position = self.positions.get(symbol)
                last_price = df.iloc[-1]['close']
                self.price_history[symbol].append(last_price)

                if position is None:
                    # No open position
                    if self.should_buy(df) and self.balances[symbol] > 0:
                        amount = self.balances[symbol] / last_price
                        print(f"Buying {symbol} amount {amount:.6f} at {last_price}")
                        # order = self.exchange.create_market_buy_order(symbol, amount)
                        self.positions[symbol] = {
                            'entry_price': last_price,
                            'amount': amount,
                            'max_price': last_price,
                        }
                        self.balances[symbol] = 0
                else:
                    entry_price = position['entry_price']
                    max_price = max(position['max_price'], last_price)
                    position['max_price'] = max_price
                    profit_ratio = (last_price - entry_price) / entry_price
                    if profit_ratio <= -0.10:
                        print(f"Stop loss selling {symbol} at {last_price}")
                        # order = self.exchange.create_market_sell_order(symbol, position['amount'])
                        self.balances[symbol] = position['amount'] * last_price
                        del self.positions[symbol]
                    elif last_price < max_price * 0.90:
                        print(f"Trailing stop selling {symbol} at {last_price}")
                        # order = self.exchange.create_market_sell_order(symbol, position['amount'])
                        self.balances[symbol] = position['amount'] * last_price
                        del self.positions[symbol]
                if self.tick % 10 == 0:
                    self.send_chart(symbol)
            time.sleep(60)


def main():
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    webhook = os.getenv('DISCORD_WEBHOOK_URL', '')
    trader = Trader(api_key, api_secret, webhook)
    trader.run()


if __name__ == '__main__':
    main()
