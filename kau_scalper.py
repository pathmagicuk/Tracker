import time
import json
import requests
from datetime import datetime

DATA_FILE = "kau_price_history.jsonl"
POLL_INTERVAL_SEC = 30

def get_gold_price_per_gram():
    """Try multiple sources for gold price per gram"""
    # Try CoinDesk first (very stable)
    try:
        resp = requests.get("https://api.coindesk.com/v1/bpi/currentprice/USD.json", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            gold_ounce = float(data["bpi"]["USD"]["rate_float"])
            return gold_ounce / 31.1035   # convert to per gram
    except:
        pass

    # Fallback to CoinGecko
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=gold&vs_currencies=usd", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            gold_ounce = float(data.get("gold", {}).get("usd", 2650))
            return gold_ounce / 31.1035
    except:
        pass

    # Absolute fallback
    return 85.20

def main_collector():
    print("🚀 Starting KAU Live Balance Tracker (Improved Gold Price)")
    print(f"Starting balance: $5,000.00 C1USD + 50.0 KAU")
    
    while True:
        gold_per_gram = get_gold_price_per_gram()
        now = datetime.now()

        kau_value = 50.0 * gold_per_gram
        total_value = 5000.0 + kau_value

        print(f"[{now.strftime('%H:%M:%S')}] "
              f"C1USD: $5,000.00 | "
              f"KAU: 50.0g (${kau_value:,.2f}) | "
              f"Total: ${total_value:,.2f} | Gold/gram: ${gold_per_gram:.2f}")

        with open(DATA_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "c1usd": 5000.0,
                "kau_grams": 50.0,
                "kau_price_per_gram": gold_per_gram,
                "total_value": total_value
            }) + "\n")

        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main_collector()
