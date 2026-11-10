import os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Bot is Alive")
        def log_message(self, *a): pass
    threading.Thread(target=HTTPServer(("0.0.0.0", port), H).serve_forever, daemon=True).start()

keep_alive()
import os, time, requests
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
URL = f"https://api.telegram.org/bot{TOKEN}"

def send(msg):
    try:
        requests.post(f"{URL}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"SENT: {msg[:40]}", flush=True)
    except Exception as e:
        print(f"send fail: {e}", flush=True)

def get_gold_price():
    # Yahoo se live GOLD price
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=15m&range=1d", headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        return closes
    except Exception as e:
        print(f"gold err: {e}", flush=True)
        return []

# --- 1. STARTUP - SIRF 1 BAAR ---
send("✅ V7.3 DEPLOY HO GAYA - 1:3 Retest Wala, Free Mode")
print("V7.3 1:3 STARTED...", flush=True)

last_update_id = 0
signal_sent_date = ""  # aaj signal bheja ya nahi, isko yaad rakhega

while True:
    try:
        # --- 2. /status CHECK - sirf jab tu bhejega ---
        r = requests.get(f"{URL}/getUpdates", params={"offset": last_update_id + 1, "timeout": 5}, timeout=15).json()
        for u in r.get("result", []):
            last_update_id = u["update_id"]
            text = u.get("message", {}).get("text", "")
            if text == "/status":
                send("✅ BOT ZINDA HAI - V7.3 1:3 Chal raha hai")

        # --- 3. GOLD SIGNAL LOGIC ---
        now_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        today = now_ist.strftime("%Y-%m-%d")
        hour_min = now_ist.hour * 60 + now_ist.minute

        # Sirf 14:30 se 20:00 ke beech check karega, aur din me 1 baar
        if 870 <= hour_min <= 1200 and signal_sent_date != today:
            prices = get_gold_price()
            if len(prices) >= 4:
                # ORB: Pehli 2 candle (14:30-15:00) ka High-Low
                orb_high = max(prices[0:2])
                orb_low = min(prices[0:2])
                live = prices[-1]

                # Retest: Price wapas ORB High ke paas aaye aur upar nikle = BUY
                # Ya ORB Low ke paas aaye aur neeche nikle = SELL
                signal = None
                if live > orb_high and abs(live - orb_high) < 5:
                    sl = orb_low
                    tp = live + (live - sl) * 3  # 1:3
                    signal = f"🟢 GOLD V7.3 BUY\nEntry: {live:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f} (1:3)\nLogic: ORB Break + Retest"
                elif live < orb_low and abs(live - orb_low) < 5:
                    sl = orb_high
                    tp = live - (sl - live) * 3
                    signal = f"🔴 GOLD V7.3 SELL\nEntry: {live:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f} (1:3)\nLogic: ORB Break + Retest"

                if signal:
                    send(signal)
                    signal_sent_date = today  # aaj ke liye lock, dobara nahi bhejega

        time.sleep(60)  # 60 sec rukega, isliye spam impossible hai

    except Exception as e:
        print(f"loop err: {e}", flush=True)
        time.sleep(60)
