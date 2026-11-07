# V7.2 FINAL - GOLD LONDON ORB + 4-PILLARS RETEST + 1:3
# FREE Render Web Service ke liye - Port wala jugad included hai

import os, time, requests
import yfinance as yf, pandas as pd
import threading
from flask import Flask

# --- 1. NAKLI WEBSITE - Render ko khush karne ke liye ---
# Ye sirf Render ko dikhane ke liye hai ki Port khula hai, bot ka kaam nahi rokega
app = Flask(__name__)
@app.route('/')
def home():
    return "V7.2 FINAL Bot Running ✅ - GOLD 1:3"
def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_flask, daemon=True).start()
# --- Jugad khatam ---

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    if TOKEN and CHAT_ID:
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        except: pass
    print(msg)

def get_data():
    df = yf.download("GC=F", period="2d", interval="15m", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

sent_orb = None
trade = None

send("✅ V7.2 FINAL START - GOLD 1:3 | Retest + Partial Booking ON")

while True:
    try:
        df = get_data()
        today = df.index[-1].date()
        day = df[df.index.date == today]
        orb = day[day.index.hour == 8]
        if len(orb) >= 2:
            orb_high = float(orb['High'].max()); orb_low = float(orb['Low'].min())
            rng = orb_high - orb_low
            key = f"{today}_{orb_high}_{orb_low}"
            if sent_orb != key and 8 <= rng <= 35:
                sent_orb = key
                send(f"🟡 GOLD ORB BAN GAYA\nHigh: {orb_high:.1f}\nLow: {orb_low:.1f}\nRange: {rng:.1f}$\nAb Breakout + Retest ka wait hai. Bina Retest ke NO ENTRY.")
            
            last = day.iloc[-1]
            price = float(last['Close']); low = float(last['Low']); high = float(last['High'])

            if trade is None and 8 <= rng <= 35:
                if price > orb_high and low <= orb_high + 1.5:
                    entry = price; sl = orb_low
                    risk = entry - sl
                    tp1 = entry + risk * 2
                    tp2 = entry + risk * 3
                    trade = {'dir':'BUY','entry':entry,'sl':sl,'tp1':tp1,'tp2':tp2,'booked':False}
                    send(f"🚀 GOLD BUY ENTRY - V7.2\nEntry: {entry:.1f}\nSL: {sl:.1f}\nTP1 (1:2): {tp1:.1f} - Yahan 50% Book\nTP2 (1:3): {tp2:.1f} - Yahan Baaki Book\nRisk: {risk:.1f}$")
                elif price < orb_low and high >= orb_low - 1.5:
                    entry = price; sl = orb_high
                    risk = sl - entry
                    tp1 = entry - risk * 2
                    tp2 = entry - risk * 3
                    trade = {'dir':'SELL','entry':entry,'sl':sl,'tp1':tp1,'tp2':tp2,'booked':False}
                    send(f"🔻 GOLD SELL ENTRY - V7.2\nEntry: {entry:.1f}\nSL: {sl:.1f}\nTP1 (1:2): {tp1:.1f}\nTP2 (1:3): {tp2:.1f}\nRisk: {risk:.1f}$")

            if trade is not None:
                d = trade['dir']
                if d == 'BUY':
                    if not trade['booked'] and high >= trade['tp1']:
                        trade['booked'] = True; trade['sl'] = trade['entry']
                        send(f"✅ GOLD TP1 HIT (1:2)\nPrice: {trade['tp1']:.1f}\n50% Profit Book Karo!\nSL ko Entry ({trade['entry']:.1f}) pe le aao. Ab NO LOSS hai.\nNext TP2: {trade['tp2']:.1f}")
                    elif trade['booked'] and high >= trade['tp2']:
                        send(f"🎉 GOLD TP2 HIT (1:3) - FULL PROFIT!\nPrice: {trade['tp2']:.1f}\nBaaki 50% bhi Book Karo. Trade Khatam.")
                        trade = None
                    elif low <= trade['sl']:
                        if trade['booked']:
                            send(f"➡️ GOLD SL TO ENTRY HIT - No Loss, TP1 Profit Safe Hai.")
                        else:
                            send(f"❌ GOLD SL HIT - Loss: {trade['entry']-trade['sl']:.1f}$")
                        trade = None
                else:
                    if not trade['booked'] and low <= trade['tp1']:
                        trade['booked'] = True; trade['sl'] = trade['entry']
                        send(f"✅ GOLD TP1 HIT (1:2)\nPrice: {trade['tp1']:.1f}\n50% Profit Book Karo!\nSL to Entry. Ab NO LOSS.")
                    elif trade['booked'] and low <= trade['tp2']:
                        send(f"🎉 GOLD TP2 HIT (1:3) - FULL PROFIT!\nPrice: {trade['tp2']:.1f}")
                        trade = None
                    elif high >= trade['sl']:
                        if trade['booked']:
                            send(f"➡️ GOLD SL TO ENTRY HIT - No Loss.")
                        else:
                            send(f"❌ GOLD SL HIT - Loss: {trade['sl']-trade['entry']:.1f}$")
                        trade = None
    except Exception as e:
        print("Error:", e)
    time.sleep(60)
