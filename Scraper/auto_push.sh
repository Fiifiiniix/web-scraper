#!/bin/bash
cd "$(dirname "$0")/.."
git add Scraper/btc_prices.csv
git commit -m "Mise à jour automatique du prix BTC"
git push
