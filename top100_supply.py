import requests
import json
import time

def get_binance_coin_symbols():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        coins = set()
        for symbol in data['symbols']:
            coins.add(symbol['baseAsset'])
        return list(coins)
    else:
        print(f"Error fetching data from Binance: {response.status_code}")
        return []

def get_top_coins():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 200,
        'page': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching top coins from CoinGecko: {response.status_code}")
        return []

def map_symbols_to_full_names(binance_symbols, top_coins):
    symbol_to_name = {}
    for coin in top_coins:
        symbol_to_name[coin['symbol'].upper()] = coin['id']
    
    full_names = {}
    for symbol in binance_symbols:
        if symbol in symbol_to_name:
            full_names[symbol] = symbol_to_name[symbol]
        else:
            print(f"Full name for symbol {symbol} not found")
    
    return full_names

def get_coin_supply(coin_id, api_key):
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": api_key
    }
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    for attempt in range(3):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            supply = data['market_data']['circulating_supply']
            print(f"{coin_id} supply is {supply}")
            time.sleep(2)  # Sleep to avoid hitting rate limits
            return supply
        else:
            print(f"Error fetching supply data for {coin_id}: {response.status_code}")
            if attempt < 2:  # Don't sleep after the last attempt
                time.sleep(10)
    return None

def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

# Fetch Binance symbols
binance_coin_symbols = get_binance_coin_symbols()

# Fetch top 100 coins by market cap
top_coins = get_top_coins()

# Map Binance symbols to full names using the top 100 coins
full_coin_names = map_symbols_to_full_names(binance_coin_symbols, top_coins)

# Add supply data to the full coin names
api_key = 'your-api'
for symbol, coin_id in full_coin_names.items():
    supply = get_coin_supply(coin_id, api_key)
    if supply is not None:
        full_coin_names[symbol] = {
            'full_name': coin_id,
            'supply': supply
        }
        # Save the full names and supplies to a JSON file after each successful fetch
        save_to_json(full_coin_names, 'binance_full_coin_names_with_supply.json')

print("Full coin names and supplies have been saved to 'binance_full_coin_names_with_supply.json'")
