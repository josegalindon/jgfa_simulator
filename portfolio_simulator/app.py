"""
Flask application for portfolio simulator
Provides API endpoints for the dashboard
"""

from flask import Flask, render_template, jsonify, request
from portfolio_engine import PortfolioEngine
import os

app = Flask(__name__)
portfolio = PortfolioEngine()


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


@app.route('/api/portfolio/update', methods=['POST'])
def update_data():
    """
    Fetch latest price data from yfinance
    Returns: JSON with update results
    """
    try:
        force_refresh = request.json.get('force_refresh', False) if request.json else False
        results = portfolio.update_price_data(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': {
                'updated_count': len(results['updated']),
                'failed_count': len(results['failed']),
                'skipped_count': len(results['skipped']),
                'updated_tickers': results['updated'],
                'failed_tickers': results['failed']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
