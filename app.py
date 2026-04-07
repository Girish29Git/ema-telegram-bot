from flask import Flask
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

TOKEN = os.getenv("TO8732483672:AAEJWmKv86uA_v2dgmbeoywYYGuvUzQpYoEKEN")
CHAT_ID = os.getenv("1051828051")

last_signal = None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def is_market_open():
    india = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india)

    if now.weekday() >= 5:
        return False

    current_time = now.time()
    return current_time >= datetime.strptime("09:30","%H:%M").time() and current_time <= datetime.strptime("15:30","%H:%M").time()

@app.route("/")
def run_bot():
    global last_signal

    if not is_market_open():
        return "Market Closed"

    data = yf.download("^NSEI", interval="5m", period="1d")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data["EMA9"] = data["Close"].ewm(span=9).mean()
    data["EMA20"] = data["Close"].ewm(span=20).mean()

    last = len(data) - 1
    prev = last - 1

    ema9_now = data["EMA9"].iloc[last]
    ema20_now = data["EMA20"].iloc[last]

    ema9_prev = data["EMA9"].iloc[prev]
    ema20_prev = data["EMA20"].iloc[prev]

    price = data["Close"].iloc[last]
    time_now = datetime.now().strftime("%H:%M:%S")

    if ema9_now > ema20_now and ema9_prev <= ema20_prev and last_signal != "BUY":
        last_signal = "BUY"
        send_telegram(f"🚨 BUY NIFTY @ {price} ⏰ {time_now}")

    elif ema9_now < ema20_now and ema9_prev >= ema20_prev and last_signal != "SELL":
        last_signal = "SELL"
        send_telegram(f"🚨 SELL NIFTY @ {price} ⏰ {time_now}")

    return "Bot Checked"