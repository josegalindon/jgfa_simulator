"""
Test script to verify benchmark tickers (SPY, IWV) work with Marketstack API
Run this before starting the main app to diagnose benchmark issues
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

API_KEY = os.getenv('MARKETSTACK_API_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = 'http://api.marketstack.com/v1'

def test_ticker(symbol, description):
    """Test if a ticker is available via Marketstack"""
    print(f"\n{'='*60}")
    print(f"Testing: {symbol} ({description})")
    print(f"{'='*60}")

    # Get data from last 30 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/eod"
    params = {
        'access_key': API_KEY,
        'symbols': symbol,
        'date_from': start_date,
        'date_to': end_date,
        'sort': 'DESC',
        'limit': 10
    }

    try:
        print(f"Fetching data from {start_date} to {end_date}...")
        response = requests.get(url, params=params, timeout=30)

        print(f"Response Status: HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'data' in data and data['data']:
                print(f"✅ SUCCESS: {symbol} is available!")
                print(f"   Data points received: {len(data['data'])}")
                print(f"   Latest price: ${data['data'][0]['close']}")
                print(f"   Latest date: {data['data'][0]['date'][:10]}")
                return True
            else:
                print(f"❌ FAILED: {symbol} returned no data")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except Exception:
                print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False


def main():
    print("\n" + "="*60)
    print("MARKETSTACK BENCHMARK TICKER TEST")
    print("="*60)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 14 else API_KEY}")
    print(f"Base URL: {BASE_URL}")

    if API_KEY == 'YOUR_API_KEY_HERE':
        print("\n❌ ERROR: Please set your Marketstack API key in .env file")
        print("   Copy .env.example to .env and add your key")
        return

    results = {}

    # Test benchmark tickers
    results['SPY'] = test_ticker('SPY', 'S&P 500 ETF')
    results['IWV'] = test_ticker('IWV', 'Russell 3000 ETF')

    # Test a known stock to verify API works
    results['AAPL'] = test_ticker('AAPL', 'Apple Inc. - Known Stock')

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"SPY (S&P 500):      {'✅ Available' if results['SPY'] else '❌ Not Available'}")
    print(f"IWV (Russell 3000): {'✅ Available' if results['IWV'] else '❌ Not Available'}")
    print(f"AAPL (Test Stock):  {'✅ Available' if results['AAPL'] else '❌ Not Available'}")
    print()

    if not results['AAPL']:
        print("⚠️  WARNING: Basic API test (AAPL) failed!")
        print("   Check your API key and plan status")
    elif not results['SPY'] or not results['IWV']:
        print("⚠️  WARNING: Benchmark tickers not available!")
        print("   Possible reasons:")
        print("   - ETFs not included in your Marketstack plan")
        print("   - Different exchange code needed")
        print("   - Plan limitations")
        print()
        print("   Recommendation: Portfolio will work but without benchmark comparison")
    else:
        print("✅ All benchmarks available! You're good to go!")

    print()


if __name__ == '__main__':
    main()
