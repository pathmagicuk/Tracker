import time
import json
import requests
import os
from datetime import datetime
import pandas as pd

# ==================== CONFIG ====================
KINESIS_ACCESS_TOKEN = os.getenv('KINESIS_ACCESS_TOKEN')  # Optional - for future Kinesis balance sync

# Starting balances
C1USD_BALANCE = 5000.0
KAU_BALANCE = 50.0                     # grams of gold

RISK_PER_TRADE = 0.005                 # 0.5% risk per trade
POLL_INTERVAL_SEC = 30

DATA_FILE = "kau_live_balance.jsonl"

def get_prices():
    """Get KAU price from metals.live (gold spot) and C1USD from CoinGecko"""
    try:
        gold = requests.get("https://api.metals.live/v1/gold", timeout=8).json()
        gold_per_gram = float(gold[0]["price"]) / 31.1035   # convert ounce to gram
        
        c1usd = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd", timeout=8).json()
        c1usd_price = float(c1usd.get("tether", {}).get("usd", 1.0))
        
        return {
            "kau_price": gold_per_gram,      # price per 1 KAU (1 gram)
            "c1usd_price": c1usd_price
        }
    except Exception as e:
        print(f"Price fetch error: {e}")
        return {"kau_price": 85.20, "c1usd_price": 1.0}   # fallback

def main():
    print("🚀 KAU Live Balance Tracker + Scalper (1:3 RR + Trailing Stop)")
    print(f"Starting balance: ${C1USD_BALANCE:,.2f} C1USD + {KAU_BALANCE:.1f} KAU")
    
    while True:
        prices = get_prices()
        now = datetime.now()

        portfolio_value = C1USD_BALANCE + (KAU_BALANCE * prices["kau_price"])

        print(f"[{now.strftime('%H:%M:%S')}] "
              f"C1USD: ${C1USD_BALANCE:,.2f} | "
              f"KAU: {KAU_BALANCE:.1f}g (${KAU_BALANCE * prices['kau_price']:,.2f}) | "
              f"Total: ${portfolio_value:,.2f}")

        # Save state
        with open(DATA_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "c1usd": C1USD_BALANCE,
                "kau_grams": KAU_BALANCE,
                "kau_price": prices["kau_price"],
                "portfolio_value": portfolio_value
            }) + "\n")

        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
