import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import pandas as pd
import openpyxl

api_passphrase = '[insert here]'
api_key = "[insert here]"
api_sec = "[insert here]"
api_url = "https://api.bitget.com"

labels = ['open time', 'open', 'high', 'low', 'close', 'ignore1', 'ignore2', 'ignore3', 'ignore4', 'ignore5', 'ignore6', 'ignore7']
labels2 = ['true range', 'atr', 'basic red line', 'basic green line', 'final red line', 'final green line', 'supertrend']

symbol = "BTC"
interval = "1h"
atr_period = 5
atr_multiplier = 0.7
limit = 1000

run_time = time.time()
time_frame = 3600


def bitget_request(requestPath, body, query, type):
    convertedbody = "{\"symbol\": \"btcusd_spbl\", \"quantity\": amount, \"side\": market_action, \"orderType\": \"market\", \"force\": \"normal\"}"
    message = str(time.time() * 1000) + type + requestPath + convertedbody + query
    encoded = message.encode()
    signature = hmac.new(base64.b64decode(api_sec), encoded, hashlib.sha256)
    signature = base64.b64encode(signature.digest())
    headers = {"ACCESS-KEY": api_key, "ACCESS-SIGN": signature.decode(), "ACCESS-TIMESTAMP": str(time.time() * 1000), "ACCESS-PASSPHRASE": api_passphrase, "Content-Type": "application/json", "locale": "English (en-US)"}
    if type == "POST":
        request_resp = requests.post((api_url + requestPath), headers=headers, data=body)
    else:
        request_resp = requests.get((api_url + requestPath), headers=headers)
    return request_resp


# coin_resp = bitget_request("/api/spot/v1/account/assets", "", "?symbol=usdt", "GET").json()
# print(coin_resp)

amount = .1
market_action = "sell"

order_resp = bitget_request("/api/spot/v1/order/order", {
        "symbol": "btcusdt_spbl",
        "quantity": amount,
        "side": market_action,
        "orderType": "market",
        "force": "normal"
    }, "", "POST")
print(order_resp)


def action(market_action):
    # Request and print out usdt balance
    usdt_resp = bitget_request("/api/spot/v1/account/assets", "", "?symbol=usdt", "GET").json()['data']['available']
    balance = usdt_resp

    # Request and print out current coin balance
    coin_resp = bitget_request("/api/spot/v1/account/assets", "", "?symbol=btc", "GET").json()['data']['available']
    tradeBalance = coin_resp

    # Request and print out current price
    current_price = requests.get("https://api.bitget.com/api/spot/v1/market/ticker?symbol=BTCUSDT_UMCBL").json()['data']['close']
    print("Current Price: " + current_price)

    if market_action == "buy":
        amount = balance / float(current_price) * 0.95
        verb = "bought"
    elif market_action == "sell":
        amount = tradeBalance
        verb = "sold"
    else:
        print("No valid actions")

    # Add order with the indicated action and volume
    # print(f"{action.capitalize()}ing {amount} of BTC at {current_price}!")
    # order_resp = bitget_request("/api/spot/v1/order/order", {
    #     "symbol": "btcusd_spbl",
    #     "quantity": amount,
    #     "side": market_action,
    #     "orderType": "market",
    #     "force": "normal"
    # }, "", "POST")
    # print(order_resp['msg'])

    # if not resp.json()['error']:
    #     print("Successfully " + verb + " BTC!")
    # else:
    #     print(f"Error: {resp.json()['error']}")


# Get Candlestick Data (OHLC) - store in dataframe
while True:
    while time.time() >= run_time:
        resp = requests.get('https://api.binance.us/api/v3/klines?symbol=' + symbol + 'USD&interval=' + interval + '&limit=' + str(limit))
        df = pd.DataFrame(resp.json())
        df.columns = labels
        df = (df[['open time', 'open', 'high', 'low', 'close']])
        df = df.astype(float)
        df2 = pd.DataFrame(columns=labels2)
        if limit == 1000:
            for i in range(limit - 1):
                for j in range(7):
                    df2.at[i, labels2[j]] = 0.0
        for i in range(limit - 1):
            if i == 0:
                i = 1
            elif i < atr_period:
                df2.at[i, labels2[0]] = max(df.at[i, labels[2]] - df.at[i, labels[3]], abs(df.at[i, labels[2]] - df.at[i, labels[1]]), abs(df.at[i, labels[3]] - df.at[i - 1, labels[4]]))
            else:
                df2.at[i, labels2[0]] = max(df.at[i, labels[2]] - df.at[i, labels[3]], abs(df.at[i, labels[2]] - df.at[i, labels[1]]), abs(df.at[i, labels[3]] - df.at[i - 1, labels[4]]))

                for j in range(atr_period):
                    df2.at[i, labels2[1]] = df2.at[i, labels2[1]] + df2.at[i - j, labels2[0]]
                df2.at[i, labels2[1]] = df2.at[i, labels2[1]] / atr_period

                df2.at[i, labels2[2]] = (df.at[i, labels[2]] + df.at[i, labels[3]]) / 2.0 + atr_multiplier * df2.at[i, labels2[1]]
                df2.at[i, labels2[3]] = (df.at[i, labels[2]] + df.at[i, labels[3]]) / 2.0 - atr_multiplier * df2.at[i, labels2[1]]

                if df2.at[i, labels2[2]] < df2.at[i - 1, labels2[4]] or df.at[i - 1, labels[4]] > df2.at[i - 1, labels2[4]]:
                    df2.at[i, labels2[4]] = df2.at[i, labels2[2]]
                else:
                    df2.at[i, labels2[4]] = df2.at[i - 1, labels2[4]]

                if df2.at[i, labels2[3]] < df2.at[i - 1, labels2[5]] or df.at[i - 1, labels[4]] > df2.at[i - 1, labels2[5]]:
                    df2.at[i, labels2[5]] = df2.at[i, labels2[3]]
                else:
                    df2.at[i, labels2[5]] = df2.at[i - 1, labels2[5]]

                if df2.at[i - 1, labels2[6]] == df2.at[i - 1, labels2[4]] and df.at[i, labels[4]] < df2.at[i, labels2[4]]:
                    df2.at[i, labels2[6]] = df2.at[i, labels2[4]]
                elif df2.at[i - 1, labels2[6]] == df2.at[i - 1, labels2[4]] and df.at[i, labels[4]] > df2.at[i, labels2[4]]:
                    df2.at[i, labels2[6]] = df2.at[i, labels2[5]]
                elif df2.at[i - 1, labels2[6]] == df2.at[i - 1, labels2[5]] and df.at[i, labels[4]] > df2.at[i, labels2[5]]:
                    df2.at[i, labels2[6]] = df2.at[i, labels2[5]]
                elif df2.at[i - 1, labels2[6]] == df2.at[i - 1, labels2[5]] and df.at[i, labels[4]] < df2.at[i, labels2[5]]:
                    df2.at[i, labels2[6]] = df2.at[i, labels2[4]]

        if df2.at[limit - 3, labels2[6]] > df.at[limit - 3, labels[4]] and df2.at[limit - 2, labels2[6]] < df.at[limit - 2, labels[4]]:
            action("buy")
        elif df2.at[limit - 3, labels2[6]] < df.at[limit - 3, labels[4]] and df2.at[limit - 2, labels2[6]] > df.at[limit - 2, labels[4]]:
            action("sell")

        run_time = run_time + time_frame
    # writer = pd.ExcelWriter('C:/Users/epcep/OneDrive/Documents/CryptoBotTest2.xlsx')
    # df2.to_excel(writer)
    # writer.save()
    time.sleep(60)