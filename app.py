from flask import Flask
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

TOKEN = os.getenv("8732483672:AAEJWmKv86uA_v2dgmbeoywYYGuvUzQpYoE")
CHAT_ID = os.getenv("1051828051")

last_signal = None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal():
    global last_signal
    data = yf.download("^NSEI", interval="5m", period="1d")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if len(data) < 25:
        return "Waiting for candles..."

    data["EMA20"] = data["Close"].ewm(span=20).mean()
    data["VWAP"] = (data["Close"] * data["Volume"]).cumsum() / data["Volume"].cumsum()
    data["RSI"] = calculate_rsi(data)

    last = len(data) - 1
    prev = last - 1

    close_now = data["Close"].iloc[last]
    close_prev = data["Close"].iloc[prev]
    ema_now = data["EMA20"].iloc[last]
    ema_prev = data["EMA20"].iloc[prev]
    vwap_now = data["VWAP"].iloc[last]
    rsi_now = data["RSI"].iloc[last]

    # BUY CALL
    if (close_now > ema_now and close_prev <= ema_prev
        and close_now > vwap_now
        and rsi_now > 55
        and last_signal != "BUY"):

        last_signal = "BUY"
        msg = f"🚨 BUY CALL @ {close_now} RSI {rsi_now}"
        send_telegram(msg)
        return msg

    # BUY PUT
    elif (close_now < ema_now and close_prev >= ema_prev
          and close_now < vwap_now
          and rsi_now < 45
          and last_signal != "SELL"):

        last_signal = "SELL"
        msg = f"🚨 BUY PUT @ {close_now} RSI {rsi_now}"
        send_telegram(msg)
        return msg

    else:
        return "No Signal"

@app.route("/")
def home():
    return get_signal()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
