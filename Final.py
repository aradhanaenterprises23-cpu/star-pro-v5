import time, requests, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- RENDER FREE WEB SERVICE KE LIYE PORT JUGAAD ---
# Render ko port chahiye, isliye ek chhota server chala rahe hai
# Isse 7$ wala Background Worker nahi lena padega
def start_dummy_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.end_headers(); self.wfile.write(b"V7.3 BOT LIVE HAI")
            def log_message(self, *a): pass
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except Exception as e:
        print("dummy server err", e)

threading.Thread(target=start_dummy_server, daemon=True).start()
# --- JUGAAD KHATAM ---

TOKEN = "APNA_TOKEN_YAHAN_DAALO"
CHAT_ID = "APNA_CHAT_ID_YAHAN_DAALO"
BASE = f"https://api.telegram.org/bot{TOKEN}"

last_trade_date = None

def send(msg):
    try:
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("send fail", e)

def check_gold():
    global last_trade_date
    try:
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()
        if last_trade_date == today:
            return
        df = yf.download("GC=F", period="5d", interval="15m", progress=False, auto_adjust=True)
        if df.empty or len(df) < 20: return
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        df['date'] = df.index.date
        df['hour'] = df.index.hour
        day = df[df['date'] == today].copy()
        if len(day) < 10: return
        orb = day[day['hour'] == 8]
        if len(orb) < 2: return
        orb_high = float(orb['High'].max())
        orb_low = float(orb['Low'].min())
        rng = orb_high - orb_low
        if rng < 8 or rng > 35: return
        after = day[day['hour'] >= 9].reset_index(drop=True)
        if len(after) < 5: return
        breakout_idx = -1; direction = None
        for i in range(len(after)):
            c = float(after['Close'].iloc[i])
            if c > orb_high:
                direction="BUY"; breakout_idx=i; break
            elif c < orb_low:
                direction="SELL"; breakout_idx=i; break
        if breakout_idx == -1: return
        entry=None; entry_idx=-1
        for j in range(breakout_idx+1, min(breakout_idx+7, len(after))):
            close=float(after['Close'].iloc[j]); low=float(after['Low'].iloc[j]); high=float(after['High'].iloc[j])
            if direction=="BUY" and low <= orb_high+1.5 and close > orb_high:
                entry=close; entry_idx=j; break
            if direction=="SELL" and high >= orb_low-1.5 and close < orb_low:
                entry=close; entry_idx=j; break
        if entry is None: return
        RR = 3
        if direction=="BUY":
            sl=orb_low; tp=entry+(entry-sl)*RR
        else:
            sl=orb_high; tp=entry-(sl-entry)*RR
        last_trade_date = today
        risk = abs(entry - sl)
        msg = f"🔥 GOLD V7.3 - 1:3 RETEST\nDirection: {direction}\nEntry: {entry:.1f}\nSL: {sl:.1f} (Risk {risk:.1f}$)\nTP: {tp:.1f} (Reward {abs(tp-entry):.1f}$)\nRR: 1:3 ✅\nORB: {orb_low:.1f} - {orb_high:.1f} Range {rng:.1f}$\nBacktest: 1:3 pe 42.9% Win, PnL +175.8$"
        send(msg)
        print("GOLD sent", msg)
    except Exception as e:
        print("gold err", e)

def check_updates():
    try:
        r = requests.get(f"{BASE}/getUpdates", params={"timeout": 5}, timeout=10).json()
        for u in r.get("result", []):
            msg = u.get("message", {})
            txt = msg.get("text", "")
            if txt == "/start":
                send("✅ GOLD V7.3 LIVE - 1:3 Retest Wala\nORB + Retest + 1:3, Backtest 175.8$")
            if txt == "/status":
                send("✅ BOT ZINDA HAI - V7.3 1:3 Chal raha hai")
    except Exception as e:
        print("poll err", e)

print("V7.3 1:3 STARTED - FREE WEB SERVICE MODE")
send("✅ V7.3 DEPLOY HO GAYA - 1:3 Retest Wala, Free Mode")

while True:
    check_updates()
    check_gold()
    time.sleep(900)
