import ccxt
import pandas as pd
import json
import time
import matplotlib.pyplot as plt

def load_coin_supply(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def fetch_historical_data(exchange, symbol, since):
    print(f"Fetching historical data for {symbol} since {pd.to_datetime(since, unit='ms')}")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', since=since)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    print(f"Fetched data for {symbol}:\n{df.head()}")
    return df

def calculate_sat_index(coin_supply, excluded_coins, days=500):
    end_time = int(time.time() * 1000)
    start_time = end_time - days * 24 * 60 * 60 * 1000  # 7 days in milliseconds
    exchange = ccxt.binance()

    total_market_cap = pd.DataFrame()

    for symbol, data in coin_supply.items():
        if symbol in excluded_coins:
            continue
        coin_id = symbol
        print(f"Processing {coin_id}")
        supply = data.get('supply', 0)
        if not supply or supply == 0:
            print(f"No supply data for {coin_id}, skipping...")
            continue
        try:
            market_data = fetch_historical_data(exchange, f'{coin_id.upper()}/USDT', start_time)
            market_data['market_cap'] = market_data['close'] * supply

            # Check for large changes in supply or price around October 8
            relevant_data = market_data[(market_data['timestamp'] >= '2024-10-06') & (market_data['timestamp'] <= '2024-10-10')]
            print(f"Relevant data for {coin_id} around October 8:\n{relevant_data[['timestamp', 'close', 'market_cap']]}")

            if len(relevant_data) > 1:
                supply_change = supply
                price_change = relevant_data['close'].pct_change().abs()
                if price_change.max() > 0.5:  # Arbitrary threshold for significant price change
                    print(f"Significant price change detected for {coin_id} on October 8")

            if total_market_cap.empty:
                total_market_cap = market_data[['timestamp', 'market_cap']]
            else:
                total_market_cap = total_market_cap.merge(market_data[['timestamp', 'market_cap']], on='timestamp', how='outer')
                total_market_cap['market_cap'] = total_market_cap['market_cap_x'].fillna(0) + total_market_cap['market_cap_y'].fillna(0)
                total_market_cap = total_market_cap.drop(columns=['market_cap_x', 'market_cap_y'])

            # Use infer_objects to ensure the correct dtype inference
            total_market_cap = total_market_cap.infer_objects(copy=False)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    total_market_cap = total_market_cap.set_index('timestamp')
    print(f"Total market cap:\n{total_market_cap.loc['2024-10-06':'2024-10-10']}")  # Print data around October 8
    return total_market_cap

def plot_sat_index(total_market_cap):
    total_market_cap.plot(title='Small Alts Total Market Cap (sat_index)')
    plt.xlabel('Date')
    plt.ylabel('Market Cap')
    plt.show()

# Load the coin supply data
coin_supply = load_coin_supply('binance_full_coin_names_with_supply.json')

# Define the coins to exclude
excluded_coins = {'BTC', 'ETH', 'BNB', 'USDT', 'FUSD', 'TUSD'}

# Calculate the sat_index
sat_index = calculate_sat_index(coin_supply, excluded_coins)

# Plot the sat_index
plot_sat_index(sat_index)
