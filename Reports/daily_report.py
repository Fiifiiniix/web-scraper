import os
import csv
import json
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "..", "Scraper", "btc_prices.csv")
output_dir = os.path.join(base_dir, "DailyReports")
os.makedirs(output_dir, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.join(output_dir, f"report-{today}.json")

try:
    with open(csv_path, "r") as f:
        rows = list(csv.reader(f))
        if not rows:
            print("[WARN] CSV vide.")
            exit()

        prices = [float(row[1]) for row in rows if len(row) >= 2]
        timestamps = [row[0] for row in rows if len(row) >= 2]

        report = {
            "count": len(prices),
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices)/len(prices),
            "first": prices[0],
            "last": prices[-1],
            "start_time": timestamps[0],
            "end_time": timestamps[-1]
        }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"[OK] Rapport généré : {output_path}")

except Exception as e:
    print(f"[ERREUR] {e}")

