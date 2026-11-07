import os
import threading
import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from flask import Flask

# --- 1. RENDER KE LIYE WEB PORT (Isse Render band nahi karega) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live - STAR PRO V5"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# --- 2. TOKEN / CHAT_ID - Dono naam chalega ---
TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# CHAT_ID ko yaad rakhne ke liye, jab tu /start bhejega to auto-save ho jayega
CURRENT_CHAT_ID = CHAT_ID
LAST_UPDATE_ID = 0

def send(msg, chat_id=None):
    target = chat_id or CURRENT_CHAT_ID or CHAT_ID
    if not TOKEN or not target:
        print("TOKEN/CHAT_ID missing in Render Env")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": target, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e)

def get_data(symbol, period="2d", interval="15m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def check_initial_balance():
    try:
        df = get_data("NQ=F", period="2d", interval="30m")
        if df is None:
            return
        high = float(df['High'].iloc[-2])
        low = float(df['Low'].iloc[-2])
        close = float(df['Close'].iloc[-1])
        if close > high:
            send(f"🔔 *STAR PRO - Umar IB Breakout*\n\n*Pair:* Nasdaq US100\n*Setup:* Initial Balance Breakout - BUY\n*Range High:* {high:.1f} toda\n*Entry:* {close:.1f}\n*SL:* {low:.1f}\n*Target:* {close + (high-low)*2:.1f}\n*Time:* {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')}")
        elif close < low:
            send(f"🔔 *STAR PRO - Umar IB Breakout*\n\n*Pair:* Nasdaq US100\n*Setup:* Initial Balance Breakdown - SELL\n*Range Low:* {low:.1f} toda\n*Entry:* {close:.1f}\n*SL:* {high:.1f}\n*Target:* {close - (high-low)*2:.1f}")
    except Exception as e:
        print("IB Error", e)

def check_gold():
    try:
        df = get_data("GC=F", period="2d", interval="1h")
        if df is None:
            return
        last = df.iloc[-1]
        prev_high = float(df['High'].iloc[-25:-1].max())
        prev_low = float(df['Low'].iloc[-25:-1].min())
        price = float(last['Close'])
        fib50 = (prev_high + prev_low) / 2
        
        if abs(price - fib50) / fib50 < 0.002:
            send(f"🔔 *STAR PRO - Gold 50% Fib*\n\n*Pair:* GOLD XAU/USD\n*Setup:* Fib 50% Retracement\n*Price:* {price:.2f}\n*Fib 50%:* {fib50:.2f}\n*Prev High:* {prev_high:.2f}\n*Prev Low:* {prev_low:.2f}\n*Bias:* BUY if upar bounce mare, SELL if neeche tode\n*SL:* {price-15:.2f} / {price+15:.2f}")
        
        if price > prev_high:
            send(f"🔔 *STAR PRO - Gold Breakout*\n\n*Pair:* GOLD\n*Setup:* Previous High Breakout - BUY\n*Price:* {price:.2f} ne {prev_high:.2f} toda")
        elif price < prev_low:
            send(f"🔔 *STAR PRO - Gold Breakdown*\n\n*Pair:* GOLD\n*Setup:* Previous Low Breakdown - SELL\n*Price:* {price:.2f} ne {prev_low:.2f} toda")
    except Exception as e:
        print("Gold Error", e)

def hourly_update():
    try:
        gold = get_data("GC=F", period="1d", interval="1h")
        nas = get_data("NQ=F", period="1d", interval="1h")
        if gold is None:
            return
        gp = float(gold['Close'].iloc[-1])
        np_ = float(nas['Close'].iloc[-1]) if nas is not None else 0
        send(f"⏰ *HOURLY UPDATE - STAR PRO*\n\n*GOLD:* ${gp:.2f}\n*NASDAQ:* {np_:.1f}\n*Time:* {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')}\n\nUmar IB + Gold Fib dono active hai. Setup bante hi alert aayega.")
    except Exception as e:
        print(e)

# --- 3. /start SUNNE WALA PART - Ye pehle nahi tha, isliye reply nahi aa raha tha ---
def listen_for_start():
    global CURRENT_CHAT_ID, LAST_UPDATE_ID
    while True:
        try:
            if not TOKEN:
                time.sleep(5)
                continue
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=20&offset={LAST_UPDATE_ID + 1}"
            r = requests.get(url, timeout=25).json()
            if not r.get("ok"):
                time.sleep(5)
                continue
            for upd in r.get("result", []):
                LAST_UPDATE_ID = upd["update_id"]
                msg = upd.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if not chat_id:
                    continue
                # Pehli baar /start aaye to usi chat ko pakad lo
                CURRENT_CHAT_ID = str(chat_id)
                if text == "/start":
                    send("✅ *STAR PRO V5 LIVE HAI BHAI*\n\nDono strategy ON hai:\n1. Umar Initial Balance - Nasdaq\n2. Gold Fib 50% + Breakout\n\nAb setup bante hi alert aayega.\n\nMarket band hai to aaj signal nahi aayega, Monday ko aayega.", chat_id=chat_id)
                elif text == "/status":
                    send("✅ *Bot Live Hai*\nGold + Nasdaq dono check ho raha hai har 15 min me.", chat_id=chat_id)
        except Exception as e:
            print("Polling Error", e)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=listen_for_start, daemon=True).start()
    # Pehle wala start msg - agar CHAT_ID pehle se hai to wahan bhi jayega
    send("✅ *STAR PRO V5 START HO GAYA*\n\nDono strategy ON hai:\n1. Umar Initial Balance - Nasdaq\n2. Gold Fib 50% + Breakout\n\nAb setup bante hi alert aayega bhai.")
    last_hourly = -1
    while True:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        check_initial_balance()
        check_gold()
        if now.minute < 15 and now.hour != last_hourly:
            hourly_update()
            last_hourly = now.hour
        time.sleep(900)
