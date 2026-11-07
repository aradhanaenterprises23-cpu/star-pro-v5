import os, time, requests, yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Render me tu ye 2 daalega, yahan mat likhna
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(msg):
    if not TOKEN or not CHAT_ID:
        print("TOKEN/CHAT_ID missing in Render Env")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e)

def get_data(symbol, period="2d", interval="15m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def check_initial_balance():
    # Umar Punjabi - Nasdaq Initial Balance - NY Open 9:30 AM ET pehle 30 min
    # Yahan hum last day ka NY session ka pehla 30 min ka High-Low le rahe hai simplified version
    try:
        df = get_data("NQ=F", period="2d", interval="30m")
        if df is None: return
        # Last candle = NY open wala range
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
    # Gold - London Session + Fib 50% + Previous High/Low
    try:
        df = get_data("GC=F", period="2d", interval="1h")
        if df is None: return
        last = df.iloc[-1]
        prev_high = float(df['High'].iloc[-25:-1].max())
        prev_low = float(df['Low'].iloc[-25:-1].min())
        price = float(last['Close'])
        fib50 = (prev_high + prev_low) / 2
        
        # Price Fib 50% ke paas aaya
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
        if gold is None: return
        gp = float(gold['Close'].iloc[-1])
        np_ = float(nas['Close'].iloc[-1]) if nas is not None else 0
        send(f"⏰ *HOURLY UPDATE - STAR PRO*\n\n*GOLD:* ${gp:.2f}\n*NASDAQ:* {np_:.1f}\n*Time:* {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')}\n\nUmar IB + Gold Fib dono active hai. Setup bante hi alert aayega.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    send("✅ *STAR PRO V5 START HO GAYA*\n\nDono strategy ON hai:\n1. Umar Initial Balance - Nasdaq\n2. Gold Fib 50% + Breakout\n\nAb setup bante hi alert aayega bhai.")
    last_hourly = -1
    while True:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        # Har 15 min pe check karo
        check_initial_balance()
        check_gold()
        # Har ghante pe 1 update
        if now.minute < 15 and now.hour != last_hourly:
            hourly_update()
            last_hourly = now.hour
        time.sleep(900) # 15 min rukega
