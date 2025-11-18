"""
Script to trigger portfolio data update via API
This will fetch all 202 tickers from Marketstack and populate the cache
"""

import requests
import time
import sys

# Your Render deployment URL
BASE_URL = "https://jgfa-simulator.onrender.com"

def reset_stuck_status():
    """Reset any stuck update status"""
    print("Step 1: Resetting any stuck update status...")
    try:
        response = requests.post(f"{BASE_URL}/api/debug/reset", timeout=10)
        result = response.json()
        if result.get('success'):
            print(f"✓ Status reset. Was stuck: {result['message']}")
            return True
        else:
            print(f"✗ Failed to reset: {result}")
            return False
    except Exception as e:
        print(f"✗ Error resetting status: {e}")
        return False

def trigger_update():
    """Trigger manual portfolio update"""
    print("\nStep 2: Triggering portfolio update...")
    print("This will fetch data for 202 tickers from Marketstack API")
    print("Expected time: 3-5 minutes (rate limited to 1 req/sec)")

    try:
        response = requests.post(
            f"{BASE_URL}/api/portfolio/update",
            headers={'Content-Type': 'application/json'},
            json={},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Update started! Fetching {result['total_tickers']} tickers...")
                return True
            else:
                print(f"✗ Update failed: {result.get('error', 'Unknown error')}")
                return False
        elif response.status_code == 400:
            result = response.json()
            print(f"✗ Update already in progress or blocked: {result.get('error')}")
            return False
        else:
            print(f"✗ HTTP {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"✗ Error triggering update: {e}")
        return False

def poll_status():
    """Poll update status until complete"""
    print("\nStep 3: Monitoring update progress...")
    print("=" * 60)

    start_time = time.time()
    last_progress = 0

    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/portfolio/update/status", timeout=10)
            result = response.json()

            if result.get('success'):
                status = result['status']

                # Show progress
                progress = status.get('progress', 0)
                total = status.get('total', 0)
                message = status.get('message', '')

                # Only print if progress changed
                if progress != last_progress:
                    elapsed = int(time.time() - start_time)
                    if total > 0:
                        pct = (progress / total) * 100
                        print(f"[{elapsed:3d}s] Progress: {progress}/{total} ({pct:.1f}%) - {message}")
                    else:
                        print(f"[{elapsed:3d}s] {message}")
                    last_progress = progress

                # Check if complete
                if not status.get('running', False):
                    print("=" * 60)
                    if status.get('error'):
                        print(f"✗ Update failed: {status['error']}")
                        return False
                    else:
                        print(f"✓ Update complete!")
                        if 'results' in status:
                            results = status['results']
                            print(f"  Updated: {len(results.get('updated', []))} tickers")
                            print(f"  Failed:  {len(results.get('failed', []))} tickers")
                            print(f"  Skipped: {len(results.get('skipped', []))} tickers")

                            if results.get('failed'):
                                print(f"\n  Failed tickers: {', '.join(results['failed'][:10])}")
                                if len(results['failed']) > 10:
                                    print(f"  ... and {len(results['failed']) - 10} more")
                        return True

            else:
                print(f"✗ Failed to get status: {result}")
                return False

        except Exception as e:
            print(f"✗ Error polling status: {e}")
            return False

        # Wait before next poll
        time.sleep(3)

def verify_data():
    """Verify data was loaded successfully"""
    print("\nStep 4: Verifying portfolio data...")
    try:
        response = requests.get(f"{BASE_URL}/api/portfolio/summary", timeout=10)
        result = response.json()

        if result.get('success') and result.get('data'):
            data = result['data']
            portfolio_value = data.get('current_value', 0)
            total_return = data.get('total_return_pct', 0)

            if portfolio_value > 0:
                print(f"✓ Portfolio loaded successfully!")
                print(f"  Portfolio Value: ${portfolio_value:,.2f}")
                print(f"  Total Return: {total_return:+.2f}%")
                print(f"  Days Active: {data.get('days_active', 0)}")
                print(f"  Latest Date: {data.get('latest_date', 'Unknown')}")
                return True
            else:
                print(f"✗ Portfolio value is zero - data may not have loaded")
                return False
        else:
            print(f"✗ Failed to fetch portfolio summary")
            return False

    except Exception as e:
        print(f"✗ Error verifying data: {e}")
        return False

def main():
    print("=" * 60)
    print("JGFA PORTFOLIO DATA UPDATE")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Date: November 14-15, 2025")
    print("=" * 60)
    print()

    # Step 1: Reset stuck status
    if not reset_stuck_status():
        print("\n⚠️  Warning: Could not reset status, but continuing anyway...")

    time.sleep(2)

    # Step 2: Trigger update
    if not trigger_update():
        print("\n❌ Failed to trigger update. Exiting.")
        print("\nTroubleshooting:")
        print("1. Check if update is already running")
        print("2. Check Render logs for errors")
        print("3. Verify API key is set correctly")
        sys.exit(1)

    time.sleep(2)

    # Step 3: Poll status
    if not poll_status():
        print("\n❌ Update did not complete successfully. Check logs.")
        sys.exit(1)

    time.sleep(2)

    # Step 4: Verify data
    if verify_data():
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Portfolio data loaded with Nov 14 prices")
        print("=" * 60)
        print(f"\nView dashboard at: {BASE_URL}")
        print()
    else:
        print("\n" + "=" * 60)
        print("⚠️  Update completed but data verification failed")
        print("=" * 60)
        print("Check the dashboard manually or review Render logs")

if __name__ == '__main__':
    main()
