"""
Flask application for portfolio simulator
Provides API endpoints for the dashboard
Automatically updates prices daily at 10pm EST
"""

from flask import Flask, render_template, jsonify, request
from portfolio_engine import PortfolioEngine
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import UPDATE_HOUR, UPDATE_MINUTE, UPDATE_TIMEZONE
import os
import threading
from datetime import datetime
import pytz

app = Flask(__name__)
portfolio = PortfolioEngine()

# Global state for tracking refresh status
refresh_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': '',
    'last_update_time': None,
    'next_scheduled_update': None
}

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone(UPDATE_TIMEZONE))
scheduler_started = False


def init_scheduler():
    """Initialize and start the scheduler for automated updates"""
    global scheduler_started

    if scheduler_started:
        return

    try:
        # Add job to run weekdays (Mon-Fri) at 10pm EST
        scheduler.add_job(
            func=scheduled_update,
            trigger=CronTrigger(
                day_of_week='mon-fri',
                hour=UPDATE_HOUR,
                minute=UPDATE_MINUTE,
                timezone=UPDATE_TIMEZONE
            ),
            id='weekday_price_update',
            name='Weekday price data update',
            replace_existing=True
        )

        # Start the scheduler
        scheduler.start()
        scheduler_started = True

        # Calculate next run time
        est_tz = pytz.timezone(UPDATE_TIMEZONE)
        next_run = scheduler.get_job('weekday_price_update').next_run_time
        refresh_status['next_scheduled_update'] = next_run.isoformat()

        print(f"✓ Scheduled weekday updates at {UPDATE_HOUR:02d}:{UPDATE_MINUTE:02d} {UPDATE_TIMEZONE} (Mon-Fri)")
        print(f"  Next update: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")


def init_data_on_startup():
    """Check if cache is empty and trigger initial data fetch if needed"""
    print(f"\nChecking data cache...")
    print(f"  Cache directory: {portfolio.cache_dir}")
    print(f"  Cache file exists: {os.path.exists(portfolio.cache_file)}")
    print(f"  Cached tickers: {len(portfolio.price_cache)}")

    if not portfolio.price_cache or len(portfolio.price_cache) == 0:
        print("="*60)
        print("FIRST-TIME SETUP: Cache is empty")
        print("Starting initial data fetch in background...")
        print("This will take 3-5 minutes for 202 tickers")
        print("NOTE: On Render, cache is lost on each deployment")
        print("="*60)

        # Start background update
        thread = threading.Thread(target=background_update, args=(False,))
        thread.daemon = True
        thread.start()
        print("Background fetch thread started")
    else:
        print(f"✓ Cache loaded: {len(portfolio.price_cache)} tickers found")
        if refresh_status.get('last_update_time'):
            print(f"  Last update: {refresh_status['last_update_time']}")


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')


@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """
    Get portfolio summary metrics
    Returns: JSON with current value, returns, P&L, risk metrics
    """
    try:
        metrics = portfolio.calculate_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/positions', methods=['GET'])
def get_positions():
    """
    Get all position details
    Returns: JSON array of position data
    """
    try:
        positions = portfolio.calculate_position_returns()

        # Separate long and short
        long_positions = [p for p in positions if p['side'] == 'Long']
        short_positions = [p for p in positions if p['side'] == 'Short']

        # Sort by P&L
        long_positions = sorted(long_positions, key=lambda x: x['pnl'], reverse=True)
        short_positions = sorted(short_positions, key=lambda x: x['pnl'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'long': long_positions,
                'short': short_positions,
                'total_positions': len(positions)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/charts', methods=['GET'])
def get_chart_data():
    """
    Get time series data for charts
    Returns: JSON with dates and various metrics
    """
    try:
        chart_data = portfolio.get_chart_data()
        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def progress_update(current, total, ticker):
    """Callback function for progress updates"""
    global refresh_status
    refresh_status['progress'] = current
    refresh_status['total'] = total
    refresh_status['message'] = f"Processing {ticker} ({current}/{total})..."


def background_update(force_refresh=False):
    """Background thread to update price data"""
    global refresh_status
    try:
        refresh_status['running'] = True
        refresh_status['message'] = 'Starting update...'

        print(f"Background update starting (force_refresh={force_refresh})...")

        results = portfolio.update_price_data(
            force_refresh=force_refresh,
            progress_callback=progress_update
        )

        # Update status with completion info
        est_tz = pytz.timezone(UPDATE_TIMEZONE)
        current_time = datetime.now(est_tz)

        refresh_status['progress'] = refresh_status['total']
        refresh_status['last_update_time'] = current_time.isoformat()
        refresh_status['message'] = f"Complete! Updated: {len(results['updated'])}, Failed: {len(results['failed'])}, Skipped: {len(results['skipped'])}"
        refresh_status['results'] = results

        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}] Price update complete: {len(results['updated'])} updated, {len(results['failed'])} failed")
    except Exception as e:
        refresh_status['message'] = f"Error: {str(e)}"
        refresh_status['error'] = str(e)
        print(f"❌ Background update error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Always set running to False, even if there's an exception
        refresh_status['running'] = False
        print(f"Background update finished. Running status set to False.")


def scheduled_update():
    """Scheduled daily update at 10pm EST"""
    print(f"Starting scheduled price update at {datetime.now(pytz.timezone(UPDATE_TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Don't start if an update is already running
    if refresh_status['running']:
        print("Update already in progress, skipping scheduled update")
        return

    # Run update in background thread
    thread = threading.Thread(target=background_update, args=(False,))
    thread.daemon = True
    thread.start()


@app.route('/api/portfolio/update', methods=['POST'])
def update_data():
    """
    Manual price data update endpoint
    Use this for initial setup or force refresh
    """
    global refresh_status

    try:
        # Check if already running
        if refresh_status['running']:
            return jsonify({
                'success': False,
                'error': 'Update already in progress',
                'status': refresh_status
            }), 400

        # Handle both JSON and empty body
        force_refresh = False
        if request.is_json and request.json:
            force_refresh = request.json.get('force_refresh', False)

        # Reset status
        refresh_status = {
            'running': True,
            'progress': 0,
            'total': len(portfolio.all_tickers),
            'message': 'Starting background update...',
            'last_update_time': refresh_status.get('last_update_time'),
            'next_scheduled_update': refresh_status.get('next_scheduled_update')
        }

        # Start background thread
        thread = threading.Thread(target=background_update, args=(force_refresh,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Update started in background',
            'total_tickers': len(portfolio.all_tickers)
        })
    except Exception as e:
        print(f"Error in update_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/update/status', methods=['GET'])
def update_status():
    """Get the status of the background update"""
    global refresh_status
    return jsonify({
        'success': True,
        'status': refresh_status
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'cache_exists': os.path.exists(portfolio.cache_file)
    })


@app.route('/api/debug/cache', methods=['GET'])
def debug_cache():
    """Debug endpoint to check cache status"""
    try:
        cache_data = {
            'cache_file_exists': os.path.exists(portfolio.cache_file),
            'cache_size': len(portfolio.price_cache),
            'tickers_in_cache': list(portfolio.price_cache.keys())[:10],  # First 10
            'sample_ticker_data': {}
        }

        # Get sample data for first ticker if available
        if portfolio.price_cache:
            first_ticker = list(portfolio.price_cache.keys())[0]
            ticker_data = portfolio.price_cache[first_ticker]
            cache_data['sample_ticker'] = first_ticker
            cache_data['sample_ticker_data'] = {
                'num_dates': len(ticker_data),
                'first_date': min(ticker_data.keys()) if ticker_data else None,
                'last_date': max(ticker_data.keys()) if ticker_data else None,
                'sample_prices': dict(list(ticker_data.items())[:3])  # First 3 dates
            }

        return jsonify({
            'success': True,
            'data': cache_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/debug/reset', methods=['POST'])
def debug_reset():
    """Reset stuck update status (emergency use only)"""
    global refresh_status

    was_stuck = refresh_status.get('running', False)

    refresh_status = {
        'running': False,
        'progress': 0,
        'total': 0,
        'message': 'Status reset',
        'last_update_time': refresh_status.get('last_update_time'),
        'next_scheduled_update': refresh_status.get('next_scheduled_update')
    }

    return jsonify({
        'success': True,
        'message': f"Status reset. Was stuck: {was_stuck}",
        'new_status': refresh_status
    })


# Check if API key is configured
def check_api_key():
    """Verify API key is set and valid"""
    api_key = portfolio.api_key

    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("\n" + "="*60)
        print("❌ ERROR: MARKETSTACK API KEY NOT CONFIGURED!")
        print("="*60)
        print("Your Marketstack API key is not set.")
        print("\nTo fix this on Render:")
        print("1. Go to: https://dashboard.render.com")
        print("2. Select your service: jgfa-simulator")
        print("3. Click 'Environment' in the sidebar")
        print("4. Add Environment Variable:")
        print("   Key:   MARKETSTACK_API_KEY")
        print("   Value: e9744c0d30d269d10d7368fa136d9c5d")
        print("5. Click 'Save Changes'")
        print("6. Wait for auto-redeploy (~1 minute)")
        print("\n" + "="*60)
        print("⚠️  APP WILL NOT WORK UNTIL API KEY IS SET!")
        print("="*60 + "\n")
        return False
    else:
        print(f"✓ API key configured: {api_key[:10]}...{api_key[-4:]}")
        return True


# Initialize scheduler and data when module is loaded (works with gunicorn)
check_api_key()
init_scheduler()
init_data_on_startup()


if __name__ == '__main__':
    print("=" * 60)
    print("Initializing Portfolio Simulator")
    print("=" * 60)

    # Update data on startup
    print("\nUpdating price data (this may take a few minutes on first run)...")
    try:
        results = portfolio.update_price_data()
        est_tz = pytz.timezone(UPDATE_TIMEZONE)
        current_time = datetime.now(est_tz)
        refresh_status['last_update_time'] = current_time.isoformat()

        print(f"✓ Updated: {len(results['updated'])} tickers")
        print(f"✗ Failed: {len(results['failed'])} tickers")
        if results['failed']:
            print(f"  Failed tickers: {', '.join(results['failed'][:10])}")
    except Exception as e:
        print(f"⚠ Warning: Error updating data on startup: {e}")

    # Scheduler already started at module load
    print(f"\n{'=' * 60}")
    print("Starting Flask Server")
    print(f"{'=' * 60}")
    print("Dashboard available at: http://127.0.0.1:5000")
    print(f"{'=' * 60}\n")

    # Use environment variable for debug mode (default to False for production)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))

    try:
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    finally:
        # Shutdown scheduler on exit
        if scheduler_started:
            scheduler.shutdown()
            print("Scheduler shut down")
