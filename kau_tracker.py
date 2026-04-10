import time
import json
import requests
from datetime import datetime
import pandas as pd

DATA_FILE = "kau_price_history.jsonl"
POLL_INTERVAL_SEC = 30

def get_coingecko_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "kinesis-velocity-token,tether,gold,silver",
            "vs_currencies": "usd"
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            gold_price_per_gram = float(data.get("gold", {}).get("usd", 2650)) / 31.1035
            
            return {
                "timestamp": datetime.now().isoformat(),
                "kvt_usd": float(data.get("kinesis-velocity-token", {}).get("usd", 472.0)),
                "c1usd_usd": float(data.get("tether", {}).get("usd", 1.0)),
                "gold_usd_per_gram": gold_price_per_gram,   # price per 1 KAU (1 gram)
                "silver_usd": float(data.get("silver", {}).get("usd", 73.18))
            }
    except Exception as e:
        print(f"CoinGecko error: {e}")
    
    # Fallback
    return {
        "timestamp": datetime.now().isoformat(),
        "kvt_usd": 472.0,
        "c1usd_usd": 1.0,
        "gold_usd_per_gram": 85.20,
        "silver_usd": 73.18,
    }

def main_collector():
    print("🚀 Starting KAU Live Balance Tracker (CoinGecko only - stable)")
    print(f"Starting balance: $5,000.00 C1USD + 50.0 KAU")
    
    while True:
        data = get_coingecko_data()
        now = datetime.now()

        kau_value = 50.0 * data["gold_usd_per_gram"]
        total_value = 5000.0 + kau_value

        print(f"[{now.strftime('%H:%M:%S')}] "
              f"C1USD: $5,000.00 | "
              f"KAU: 50.0g (${kau_value:,.2f}) | "
              f"Total: ${total_value:,.2f}")

        # Save to file
        with open(DATA_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": data["timestamp"],
                "c1usd": 5000.0,
                "kau_grams": 50.0,
                "kau_price_per_gram": data["gold_usd_per_gram"],
                "total_value": total_value
            }) + "\n")

        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main_collector()
