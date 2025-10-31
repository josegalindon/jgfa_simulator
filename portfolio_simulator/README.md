# Long-Short Portfolio Simulator

A comprehensive web-based portfolio simulator for tracking a market-neutral long-short equal-weight strategy with daily updates using real-time market data.

## Portfolio Strategy

**Strategy Type:** Long-Short Equal-Weight Market Neutral

- **Long Position:** 100 stocks (top 100 companies by composite score)
- **Short Position:** 100 stocks (bottom 100 companies by composite score)
- **Position Size:** 1% per position (equal weight)
- **Net Exposure:** Market neutral (100% long, 100% short)
- **Initial Capital:** $100,000
- **Inception Date:** January 2, 2024

## Features

### Core Functionality
- ✅ Daily price updates via yfinance API
- ✅ Portfolio performance tracking from inception
- ✅ Individual position P&L for both long and short sides
- ✅ Intelligent data caching to minimize API calls
- ✅ Graceful handling of market closures (weekends/holidays)

### Performance Metrics
- Total portfolio return (dollar amount and percentage)
- Long side vs Short side P&L breakdown
- Annualized volatility
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- Comparison vs S&P 500 benchmark

### Visualizations
- Cumulative returns chart (portfolio vs benchmark)
- Daily portfolio value chart
- Daily returns distribution
- Drawdown chart
- Best/worst performing positions

### Interactive Dashboard
- Real-time data refresh button
- Searchable and sortable position tables
- Separate views for long and short positions
- Responsive design for mobile and desktop

## Project Structure

```
portfolio_simulator/
├── app.py                  # Flask application and API endpoints
├── config.py               # Portfolio configuration and ticker arrays
├── portfolio_engine.py     # Portfolio calculation engine
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Data cache directory (auto-created)
│   └── price_cache.json   # Cached price data
├── templates/
│   └── index.html         # Dashboard HTML template
└── static/
    ├── style.css          # Dashboard CSS styling
    └── app.js             # Frontend JavaScript
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for fetching market data

### Step 1: Clone or Download the Project

Navigate to the project directory:
```bash
cd portfolio_simulator
```

### Step 2: Install Dependencies

Install required Python packages:
```bash
pip install -r requirements.txt
```

### Step 3: Initial Data Setup

The application will automatically fetch historical data on first run. This may take several minutes depending on your internet connection.

## Running the Application

### Start the Flask Server

```bash
python app.py
```

On startup, the application will:
1. Load the ticker arrays from config
2. Fetch historical price data from yfinance (if not cached)
3. Start the Flask web server on port 5000

### Access the Dashboard

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

Or from another device on the same network:
```
http://<your-ip-address>:5000
```

## Usage Guide

### Dashboard Overview

**Summary Cards** - Display key portfolio metrics:
- Current portfolio value
- Total P&L with long/short breakdown
- Sharpe ratio
- Maximum drawdown and volatility

**Benchmark Comparison** - Shows portfolio performance vs S&P 500

**Charts Section** - Four interactive charts:
1. Cumulative Returns (portfolio vs benchmark)
2. Portfolio Value over time
3. Daily Returns distribution
4. Drawdown chart

**Best/Worst Performers** - Top 5 and bottom 5 positions by P&L

**Position Tables** - Detailed view of all 200 positions:
- Searchable by ticker
- Sortable by P&L, return %, or ticker
- Separate tabs for long and short positions

### Refreshing Data

Click the **"Refresh Data"** button to fetch the latest prices from Yahoo Finance. The application will:
- Only fetch data for dates not already cached
- Update all positions with current prices
- Recalculate portfolio metrics
- Update all charts and tables

**Note:** Market data is only available on trading days. The application will show the most recent closing prices.

## Data Caching

The application uses a smart caching system to minimize API calls:

- **Cache Location:** `data/price_cache.json`
- **Cache Strategy:** Only fetches new data since last update
- **Benefits:**
  - Faster load times
  - Reduces API rate limits
  - Works offline for previously cached dates

To force a full refresh, delete the cache file and restart the application.

## Error Handling

The application handles common issues gracefully:

### Missing or Delisted Tickers
- Positions with no data will be skipped
- Failed tickers are logged in the console
- Portfolio calculations continue with available data

### API Rate Limits
- yfinance has generous rate limits but can throttle excessive requests
- The caching system minimizes API calls
- Spread out refresh clicks if encountering rate limits

### Market Closures
- Weekend/holiday data shows last available closing prices
- No errors are thrown for non-trading days

## API Endpoints

The application provides REST API endpoints:

### GET `/api/portfolio/summary`
Returns portfolio summary metrics
```json
{
  "success": true,
  "data": {
    "current_value": 105234.56,
    "total_return_pct": 5.23,
    "long_pnl": 3456.78,
    "short_pnl": 1777.78,
    ...
  }
}
```

### GET `/api/portfolio/positions`
Returns all position details
```json
{
  "success": true,
  "data": {
    "long": [...],
    "short": [...],
    "total_positions": 200
  }
}
```

### GET `/api/portfolio/charts`
Returns time series data for charts
```json
{
  "success": true,
  "data": {
    "dates": [...],
    "portfolio_values": [...],
    "portfolio_returns": [...],
    ...
  }
}
```

### POST `/api/portfolio/update`
Triggers data refresh from yfinance
```json
{
  "success": true,
  "data": {
    "updated_count": 150,
    "failed_count": 2,
    "skipped_count": 48
  }
}
```

## Customization

### Changing the Ticker Lists

Edit `config.py` to modify:
- `TOP_100` - Long positions
- `BOTTOM_100` - Short positions
- `INITIAL_CAPITAL` - Starting capital
- `INCEPTION_DATE` - Portfolio start date
- `BENCHMARK_TICKER` - Comparison benchmark

### Modifying Position Size

The current implementation uses equal weights (1% per position). To change:
1. Edit `POSITION_SIZE` in `config.py`
2. Adjust calculations in `portfolio_engine.py` if needed

### Adding Custom Metrics

Extend the `calculate_metrics()` method in `portfolio_engine.py` to add:
- Information ratio
- Sortino ratio
- Beta
- Other custom metrics

## Troubleshooting

### Application won't start
- Check Python version: `python --version` (must be 3.8+)
- Verify all dependencies installed: `pip list`
- Check for port conflicts (port 5000)

### No data showing
- Check internet connection
- Verify ticker symbols are valid
- Check console for error messages
- Delete `data/price_cache.json` and restart

### Slow performance
- First load fetches all historical data (slow)
- Subsequent loads use cache (fast)
- Consider reducing the date range in config

### Charts not displaying
- Check browser console for JavaScript errors
- Verify Chart.js CDN is accessible
- Try a different browser

## Technical Stack

- **Backend:** Python Flask
- **Data Source:** yfinance (Yahoo Finance API)
- **Data Processing:** pandas, numpy
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Charts:** Chart.js 4.4.0
- **Storage:** JSON file-based cache

## Performance Considerations

- Initial data fetch: 5-10 minutes (200 tickers, ~1 year of data)
- Subsequent loads: <5 seconds (using cache)
- Daily refresh: 1-2 minutes (only fetches new data)
- Memory usage: ~100-200 MB (depending on data volume)

## Limitations

- **Data Source:** Relies on Yahoo Finance data availability
- **Real-time:** Shows end-of-day closing prices (not intraday)
- **Historical Data:** Limited to data available from yfinance
- **Delisted Stocks:** May have incomplete data
- **Corporate Actions:** Adjusted close prices account for splits/dividends

## Future Enhancements

Potential features for future versions:
- [ ] Intraday price updates
- [ ] Portfolio rebalancing simulation
- [ ] Transaction cost modeling
- [ ] Tax-aware calculations
- [ ] Multiple portfolio comparison
- [ ] Export to CSV/Excel
- [ ] Email alerts for significant moves
- [ ] Database backend (PostgreSQL/SQLite)

## License

This project is provided as-is for educational and research purposes.

## Support

For issues or questions:
1. Check this README
2. Review console logs for errors
3. Verify all dependencies are installed
4. Test with a smaller ticker list first

## Acknowledgments

- Market data provided by Yahoo Finance via yfinance
- Chart visualizations powered by Chart.js
- Flask web framework by Pallets Projects

---

**Disclaimer:** This simulator is for educational purposes only. Past performance does not guarantee future results. Always do your own research before making investment decisions.
