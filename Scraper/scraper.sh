#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="$SCRIPT_DIR/btc_prices.csv"
URL="https://www.okx.com/priapi/v5/market/candles?instId=BTC-USDT&limit=1&bar=1m"

JSON=$(curl -s -H "User-Agent: Mozilla/5.0" "$URL")

if [[ -z "$JSON" ]]; then
    echo "Erreur : Impossible de récupérer les données."
    exit 1
fi

PRICE=$(echo "$JSON" | grep -oP '\[.*?\]' | head -1 | awk -F',' '{gsub(/"/, "", $5); print $5}')
DATE=$(date +"%Y-%m-%d %H:%M:%S")

if [[ -n "$PRICE" ]]; then
    echo "$DATE,$PRICE" >> "$CSV_FILE"
    echo "[OK] $DATE : $PRICE USD"
else
    echo "Erreur : Prix non récupéré"
fi
