import time
import json
import requests
import os
from datetime import datetime
import numpy as np

# ==================== CONFIG ====================
C1USD_BALANCE = 5000.0
KAU_BALANCE = 50.0                    # grams

RISK_PER_TRADE = 0.005                # 0.5% risk per trade
POLL_INTERVAL_SEC = 30

DATA_FILE = "kau_trades_log.jsonl"

# Strategy parameters
RSI_LONG = 60
RSI_SHORT = 40
ATR_PERIOD = 14
LOOKBACK_BARS = 8
RR_RATIO = 3.0
TRAIL_ACTIVATION = 1.5
TRAIL_DISTANCE = 1.0

kau_prices = []   # rolling window for ATR and breakouts

def get_prices():
    try:
        gold = requests.get("https://api.metals.live/v1/gold", timeout=8).json()
        gold_per_gram = float(gold[0]["price"]) / 31.1035
        
        c1 = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd", timeout=8).json()
        c1_price = float(c1.get("tether", {}).get("usd", 1.0))
        
        return gold_per_gram, c1_price
    except:
        return 85.20, 1.0   # fallback

def calculate_atr(prices, period=ATR_PERIOD):
    if len(prices) < period + 1:
        return 0.0
    tr = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    return np.mean(tr[-period:])

def generate_signal(current_price, atr):
    if len(kau_prices) < LOOKBACK_BARS + 1 or atr == 0:
        return None
    
    recent_high = max(kau_prices[-LOOKBACK_BARS:])
    recent_low = min(kau_prices[-LOOKBACK_BARS:])
    
    # Simple RSI approximation for signal strength
    rsi = 50  # placeholder - can be improved later
    
    if current_price > recent_high and rsi > RSI_LONG:
        return "BUY"
    elif current_price < recent_low and rsi < RSI_SHORT:
        return "SELL"
    return None

def execute_trade(signal, current_price, atr):
    global C1USD_BALANCE, KAU_BALANCE
    
    risk_amount = C1USD_BALANCE * RISK_PER_TRADE
    stop_distance = atr
    position_size_grams = risk_amount / stop_distance   # how many grams to buy/sell
    
    if signal == "BUY":
        cost = position_size_grams * current_price
        if cost > C1USD_BALANCE:
            cost = C1USD_BALANCE
            position_size_grams = cost / current_price
        C1USD_BALANCE -= cost
        KAU_BALANCE += position_size_grams
        print(f"BUY EXECUTED: +{position_size_grams:.2f} KAU at ${current_price:.2f}/g | Cost: ${cost:.2f}")
        
    elif signal == "SELL":
        if position_size_grams > KAU_BALANCE:
            position_size_grams = KAU_BALANCE
        proceeds = position_size_grams * current_price
        KAU_BALANCE -= position_size_grams
        C1USD_BALANCE += proceeds
        print(f"SELL EXECUTED: -{position_size_grams:.2f} KAU at ${current_price:.2f}/g | Proceeds: ${proceeds:.2f}")

def main():
    print("🚀 KAU Live Scalper + Balance Tracker Started")
    print(f"Starting: ${C1USD_BALANCE:,.2f} C1USD + {KAU_BALANCE:.1f} KAU")
    
    while True:
        kau_price, c1_price = get_prices()
        kau_prices.append(kau_price)
        if len(kau_prices) > 100:
            kau_prices.pop(0)

        atr = calculate_atr(kau_prices)
        signal = generate_signal(kau_price, atr)

        now = datetime.now()
        portfolio_value = C1USD_BALANCE + (KAU_BALANCE * kau_price)

        print(f"[{now.strftime('%H:%M:%S')}] "
              f"C1USD: ${C1USD_BALANCE:,.2f} | "
              f"KAU: {KAU_BALANCE:.1f}g (${KAU_BALANCE * kau_price:,.2f}) | "
              f"Total: ${portfolio_value:,.2f} | ATR: {atr:.4f}")

        if signal:
            print(f"[{now.strftime('%H:%M:%S')}] SIGNAL: {signal} | Price: ${kau_price:.2f}/g")
            execute_trade(signal, kau_price, atr)

        with open(DATA_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "c1usd": C1USD_BALANCE,
                "kau_grams": KAU_BALANCE,
                "kau_price": kau_price,
                "signal": signal,
                "portfolio_value": portfolio_value
            }) + "\n")

        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
