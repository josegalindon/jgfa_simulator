"""
Flask application for portfolio simulator
Provides API endpoints for the dashboard
"""

from flask import Flask, render_template, jsonify, request
from portfolio_engine import PortfolioEngine
import os
import threading

app = Flask(__name__)
portfolio = PortfolioEngine()

# Global state for tracking refresh status
refresh_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': ''
}


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


def background_update(force_refresh=False):
    """Background thread to update price data"""
    global refresh_status
    try:
        refresh_status['running'] = True
        refresh_status['message'] = 'Starting update...'

        results = portfolio.update_price_data(force_refresh=force_refresh)

        refresh_status['running'] = False
        refresh_status['message'] = f"Complete! Updated {len(results['updated'])} tickers"
        refresh_status['results'] = results
    except Exception as e:
        refresh_status['running'] = False
        refresh_status['message'] = f"Error: {str(e)}"
        refresh_status['error'] = str(e)


@app.route('/api/portfolio/update', methods=['POST'])
def update_data():
    """
    Start background price data update
    Returns immediately while update runs in background
    """
    global refresh_status

    try:
        # Check if already running
        if refresh_status['running']:
            return jsonify({
                'success': False,
                'error': 'Update already in progress'
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
            'message': 'Starting background update...'
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


if __name__ == '__main__':
    # Update data on startup
    print("Initializing portfolio simulator...")
    print("Updating price data (this may take a few minutes on first run)...")

    try:
        results = portfolio.update_price_data()
        print(f"Updated: {len(results['updated'])} tickers")
        print(f"Failed: {len(results['failed'])} tickers")
        if results['failed']:
            print(f"Failed tickers: {results['failed'][:10]}")  # Show first 10
    except Exception as e:
        print(f"Warning: Error updating data on startup: {e}")

    print("\nStarting Flask server...")
    print("Dashboard available at: http://127.0.0.1:5000")

    # Use environment variable for debug mode (default to False for production)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
