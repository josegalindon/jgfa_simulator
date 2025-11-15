#!/bin/bash

echo "============================================"
echo "Portfolio Simulator - Reset and Run"
echo "============================================"
echo ""

echo "Step 1: Clearing old cache..."
if [ -f "data/price_cache.json" ]; then
    rm data/price_cache.json
    echo "  - Old cache deleted"
else
    echo "  - No cache found (clean start)"
fi
echo ""

echo "Step 2: Installing dependencies..."
pip install -r requirements.txt
echo ""

echo "Step 3: Starting Flask server..."
echo "============================================"
echo "IMPORTANT: After server starts:"
echo "1. Open browser to http://127.0.0.1:5000"
echo "2. Press Ctrl+F5 (or Cmd+Shift+R on Mac) to hard refresh"
echo "3. Wait for initial data load (3-5 minutes for 202 tickers)"
echo "============================================"
echo ""
python app.py
