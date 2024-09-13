import requests
import pandas as pd
import os 

def get_tickers():

    # Binance API endpoint for 24hr ticker price change statistics
    url = "https://api.binance.com/api/v3/ticker/24hr"

    # Fetch data
    response = requests.get(url)
    tickers = response.json()

    # Filter tickers with volume > 1 million
    threshold_volume = 10_000_000
    high_volume_tickers = [ticker for ticker in tickers if (float(ticker['quoteVolume']) > threshold_volume and "USDT" in ticker['symbol'] and ticker['symbol'][:4] != "USDT")]

    sorted_tickers = sorted(high_volume_tickers, key=lambda x: float(x['quoteVolume']), reverse=True)


    tickers_filtered = [ticker['symbol'] for ticker in sorted_tickers]
    
    print(f"no of tickers: {len(tickers_filtered)}")
    return tickers_filtered


# Function to get Binance symbol info
def get_binance_symbol_info(symbol):
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    for s in data['symbols']:
        if s['symbol'] == symbol:
            return s
    return None

# Function to get Bybit symbol info
def get_bybit_symbol_info(symbol):
    url = "https://api.bybit.com/v5/market/instruments-info?category=spot"
    response = requests.get(url)
    data = response.json()

    for s in data['result']['list']:
        if s['symbol'] == symbol:
            return s
    return None

# Function to get the current price of a symbol in USDT
def get_current_price(symbol, exchange):
    if exchange == 'binance':
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    elif exchange == 'bybit':
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    
    if exchange == 'binance':
        try:
            print(f"{exchange}, {symbol} , {float(data['price'])}")
            return float(data['price'])
        except:
            return 0
    elif exchange == 'bybit':
        try:
            print(f"{exchange}, {symbol} ,{float(data['result']['list'][0]['lastPrice'])}")
            return float(data['result']['list'][0]['lastPrice'])
        except:
            return 0
    
def main():
    # Define the ticker symbol you're interested in (example: XUSDT)
    tickers = get_tickers()

    # Prepare the data
    data_binance = []
    data_bybit = []

    for ticker in tickers:
        # Binance data
        binance_info = get_binance_symbol_info(ticker)
        binance_price = get_current_price(ticker, 'binance')

        if binance_info and binance_price != 0:
            print("binance go")
            max_order_size_native = float(binance_info['filters'][1]['maxQty'])  
            max_stop_order_size_native = float(binance_info['filters'][3]['maxQty']) 
            
            max_order_size_usd = max_stop_order_size_native * binance_price
            max_stop_order_size_usd = max_stop_order_size_native * binance_price
            

            if not binance_info['filters'][6]['applyMaxToMarket']:
                max_order_notional = float(binance_info['filters'][6]['maxNotional'])
                max_order_notional_native = max_order_notional / binance_price
                max_stop_order_notional = max_stop_order_size_native * binance_price
                max_stop_order_notional_native = max_stop_order_size_native
            else:
                max_order_notional = binance_info['filters'][6]['maxNotional']
                max_order_notional_native = max_order_notional / binance_price
                max_stop_order_notional = binance_info['filters'][6]['maxNotional']
                max_stop_order_notional_native = max_stop_order_notional / binance_price
                
        if max_order_size_usd < max_order_notional:
            max_order = max_order_size_usd
            max_order_native = max_order_size_native
        else:
            max_order = max_order_notional
            max_order_native = max_order_notional_native
            
        if max_stop_order_size_usd < max_stop_order_notional:
            max_stop_order = max_stop_order_size_usd
            max_stop_order_native = max_stop_order_size_native
        else:
            max_stop_order = max_stop_order_notional
            max_stop_order_native = max_stop_order_notional_native

            #max_order, max_order_native, max_stop_order_max_stop_order_native
            data_binance.append([f"{ticker} (Binance)", max_order_native, max_order,max_stop_order_native, max_stop_order])

        # Bybit data
        bybit_info = get_bybit_symbol_info(ticker)
        bybit_price = get_current_price(ticker, 'bybit')

        if bybit_info and bybit_price != 0:
            print("bybit go")
            max_order_size_native = float(bybit_info['lotSizeFilter']['maxOrderQty'])
            max_stop_order_size_native = float(bybit_info['lotSizeFilter']['maxOrderQty'])  # Assuming same as max order size

            max_order_size_usd = max_order_size_native * bybit_price
            max_stop_order_size_usd = max_stop_order_size_native * bybit_price
            
            max_order_notional = float(bybit_info['lotSizeFilter']['maxOrderAmt'])
            max_order_notional_native = max_order_notional / bybit_price
            max_stop_order_notional = float(bybit_info['lotSizeFilter']['maxOrderAmt'])
            max_stop_order_notional_native = max_stop_order_notional / bybit_price
            
        if max_order_size_usd < max_order_notional:
            max_order = max_order_size_usd
            max_order_native = max_order_size_native
        else:
            max_order = max_order_notional
            max_order_native = max_order_notional_native
            
        if max_stop_order_size_usd < max_stop_order_notional:
            max_stop_order = max_stop_order_size_usd
            max_stop_order_native = max_stop_order_size_native
        else:
            max_stop_order = max_stop_order_notional
            max_stop_order_native = max_stop_order_notional_native

            data_bybit.append([f"{ticker} (Bybit)", max_order_native, max_order,max_stop_order_native, max_stop_order])

    # Create a DataFrame and save to Excel
    df_binance = pd.DataFrame(data_binance, columns=['Ticker', 'Max Buy/Sell Order Size (Native)', 'Max Buy/Sell Order Size (USD)','Max Stop Order Size (Native)', 'Max Stop Order Size (USD)'])
    df_bybit = pd.DataFrame(data_bybit, columns=['Ticker','Max Buy/Sell Order Size (Native)', 'Max Buy/Sell Order Size (USD)','Max Stop Order Size (Native)', 'Max Stop Order Size (USD)'])

    df = pd.concat([df_binance,df_bybit], axis = 0)

    print(df)
    # Save to Excel
    output_file = 'order_sizes.xlsx'
    
    #df = df.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x)

    #df.to_csv(output_file, index=False, header= True)
    
    df_binance = df_binance.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x)
    df_bybit = df_bybit.applymap(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x)

    
    with pd.ExcelWriter(output_file) as writer:
        df_binance.to_excel(writer, sheet_name="Binance", index = False)
        df_bybit.to_excel(writer, sheet_name="Bybit", index = False)
        

    print(f"Excel file saved as {output_file}")


if __name__ == "__main__":
    main()
