======================================================
# MEGA AUTO TRADING BOT (DEMO + REAL)
# Bybit Futures | Telegram Control | Risk Engine
# Cloud Ready (Render)
# ======================================================

import os, time, threading, requests
from datetime import datetime
from pybit.unified_trading import HTTP

# =====================
# ENV CONFIG
# =====================
MODE = os.getenv("MODE", "DEMO")  # DEMO / REAL

DEMO_KEY = os.getenv("xllZwqnoAezxW7zWXQ")
DEMO_SECRET = os.getenv("RKItQAbFxuzpDV06D4rGAau2ywmYqGsy4Uj6")

REAL_KEY = os.getenv("DDVfrKX58oJq8Eb1Bp")
REAL_SECRET = os.getenv("IbhLHwJstUtNyUzSQxMaaU5Jp6wc3CGEMRto")

TG_TOKEN = os.getenv("8386423650:AAGAk3-bEA10mjJDdiM9O1282syvnQYvhMY")
TG_ADMIN = int(os.getenv("7662870482")

if MODE == "REAL":
    API_KEY = REAL_KEY
    API_SECRET = REAL_SECRET
    TESTNET = False
else:
    API_KEY = DEMO_KEY
    API_SECRET = DEMO_SECRET
    TESTNET = True

# =====================
# BOT SETTINGS
# =====================
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
LEVERAGE = 20
RISK_PER_TRADE = 0.20     # 20%
MAX_DAILY_LOSS = 0.10     # 10%
MAX_DAILY_PROFIT = 0.25  # 25%
MAX_TRADES = 5

START_DAY_BALANCE = None
TRADES_TODAY = 0
BOT_ACTIVE = True
KILL_SWITCH = False

# =====================
# BYBIT SESSION
# =====================
session = HTTP(
    testnet=TESTNET,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# =====================
# TELEGRAM
# =====================
def tg(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_ADMIN, "text": msg}
        )
    except:
        pass

# =====================
# BALANCE
# =====================
def get_balance():
    r = session.get_wallet_balance(accountType="UNIFIED")
    return float(r["result"]["list"][0]["totalWalletBalance"])

# =====================
# SIMPLE STRATEGY
# =====================
def signal(symbol):
    """
    Placeholder strategy
    Replace later with AI / indicators
    """
    t = int(time.time())
    if t % 2 == 0:
        return "BUY"
    return "SELL"

# =====================
# ORDER
# =====================
def open_trade(symbol, side):
    global TRADES_TODAY

    bal = get_balance()
    qty_usdt = bal * RISK_PER_TRADE
    price = float(session.get_tickers(category="linear", symbol=symbol)
                  ["result"]["list"][0]["lastPrice"])
    qty = round(qty_usdt / price, 3)

    session.set_leverage(
        category="linear",
        symbol=symbol,
        buyLeverage=LEVERAGE,
        sellLeverage=LEVERAGE
    )

    session.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        orderType="Market",
        qty=qty,
        timeInForce="IOC"
    )

    TRADES_TODAY += 1
    tg(f"📈 {side} {symbol} | qty={qty}")

# =====================
# DAILY RISK CHECK
# =====================
def risk_check():
    global KILL_SWITCH
    bal = get_balance()
    pnl = (bal - START_DAY_BALANCE) / START_DAY_BALANCE

    if pnl <= -MAX_DAILY_LOSS:
        KILL_SWITCH = True
        tg("🛑 DAILY LOSS LIMIT HIT")
    if pnl >= MAX_DAILY_PROFIT:
        KILL_SWITCH = True
        tg("🎯 DAILY TARGET HIT")

# =====================
# MAIN LOOP
# =====================
def trader():
    global START_DAY_BALANCE, TRADES_TODAY, KILL_SWITCH

    START_DAY_BALANCE = get_balance()
    tg(f"🚀 BOT STARTED | {MODE} | Balance: {START_DAY_BALANCE}")

    while True:
        if not BOT_ACTIVE or KILL_SWITCH:
            time.sleep(10)
            continue

        if TRADES_TODAY >= MAX_TRADES:
            time.sleep(30)
            continue

        risk_check()

        for sym in SYMBOLS:
            if KILL_SWITCH:
                break
            sig = signal(sym)
            open_trade(sym, sig)
            time.sleep(5)

        time.sleep(15)

# =====================
# TELEGRAM COMMANDS
# =====================
def telegram_listener():
    offset = None
    global BOT_ACTIVE, KILL_SWITCH

    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30}
            ).json()

            for u in r["result"]:
                offset = u["update_id"] + 1
                if "message" not in u:
                    continue
                if u["message"]["chat"]["id"] != TG_ADMIN:
                    continue

                txt = u["message"]["text"].lower()

                if txt == "/stop":
                    BOT_ACTIVE = False
                    tg("⛔ Bot stopped")
                elif txt == "/start":
                    BOT_ACTIVE = True
                    KILL_SWITCH = False
                    tg("▶️ Bot started")
                elif txt == "/status":
                    bal = get_balance()
                    tg(f"⚙️ Mode:{MODE}\nBalance:{bal}\nTrades:{TRADES_TODAY}")

        except:
            pass

        time.sleep(5)

# =====================
# RUN
# =====================
threading.Thread(target=telegram_listener, daemon=True).start()
trader()
