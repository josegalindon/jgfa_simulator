"""
Portfolio calculation engine for long-short equal-weight strategy
Handles price data fetching, caching, and performance metrics
"""

import requests
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from config import (
    TOP_100, BOTTOM_100, INITIAL_CAPITAL, INCEPTION_DATE,
    SP500_TICKER, RUSSELL3000_TICKER, POSITION_SIZE,
    MARKETSTACK_API_KEY, MARKETSTACK_BASE_URL, MARKETSTACK_REQUESTS_PER_SECOND
)


class PortfolioEngine:
    def __init__(self, cache_dir='data'):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'price_cache.json')
        self.long_tickers = TOP_100
        self.short_tickers = BOTTOM_100
        self.all_tickers = TOP_100 + BOTTOM_100 + [SP500_TICKER, RUSSELL3000_TICKER]
        self.sp500_ticker = SP500_TICKER
        self.russell3000_ticker = RUSSELL3000_TICKER
        self.initial_capital = INITIAL_CAPITAL
        self.inception_date = INCEPTION_DATE
        self.position_size = POSITION_SIZE
        self.api_key = MARKETSTACK_API_KEY
        self.base_url = MARKETSTACK_BASE_URL

        # Rate limiting: Basic plan has 10,000 requests/month
        # 1 request per second is safe and won't hit API rate limits
        self.min_request_interval = 1.0 / MARKETSTACK_REQUESTS_PER_SECOND
        self.last_request_time = 0

        # Ticker mapping for indices (Yahoo format -> Marketstack format)
        # Marketstack uses standard ticker symbols (no special prefixes for indices)
        self.ticker_map = {
            '^GSPC': 'SPY',   # S&P 500 ETF as proxy (Marketstack doesn't support ^GSPC directly)
            '^RUA': 'IWV'     # Russell 3000 ETF as proxy
        }

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Load cached data
        self.price_cache = self._load_cache()

    def _load_cache(self):
        """Load price data from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save price data to cache file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.price_cache, f)

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _map_ticker(self, ticker):
        """Map Yahoo Finance tickers to Marketstack tickers"""
        return self.ticker_map.get(ticker, ticker)

    def _fetch_ticker_data(self, ticker, start_date, end_date, max_retries=3):
        """Fetch historical price data from Marketstack API"""
        # Map ticker if needed (for indices)
        marketstack_ticker = self._map_ticker(ticker)

        for attempt in range(max_retries):
            try:
                # Add delay before retry attempts
                if attempt > 0:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    print(f"Retrying {ticker} after {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)

                # Enforce rate limiting
                self._rate_limit()

                # Build Marketstack API URL
                url = f"{self.base_url}/eod"
                params = {
                    'access_key': self.api_key,
                    'symbols': marketstack_ticker,
                    'date_from': start_date,
                    'date_to': end_date,
                    'sort': 'ASC',
                    'limit': 1000  # Maximum results per request
                }

                # Make API request
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    # Check if we have data
                    if not data.get('data'):
                        if attempt == max_retries - 1:
                            print(f"No data for {ticker}")
                        continue

                    # Convert Marketstack format to our format
                    prices = {}
                    for bar in data['data']:
                        # Marketstack date format: "2024-01-01T00:00:00+0000"
                        # Extract just the date part
                        date_str = bar['date'][:10]  # Get YYYY-MM-DD
                        prices[date_str] = float(bar['close'])  # close price

                    return prices

                elif response.status_code == 429:
                    # Rate limit hit, wait longer
                    print(f"Rate limit hit for {ticker}, waiting 60s...")
                    time.sleep(60)
                    continue
                else:
                    if attempt == max_retries - 1:
                        print(f"API error for {ticker}: {response.status_code}")
                        # Try to get error details
                        try:
                            error_data = response.json()
                            print(f"Error details: {error_data}")
                        except:
                            pass
                    continue

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error fetching {ticker}: {str(e)[:100]}")
                continue

        return None

    def update_price_data(self, force_refresh=False, progress_callback=None):
        """
        Update price data for all tickers
        Only fetches most recent end of day price to minimize API calls
        progress_callback: Optional function to call with (current, total, ticker) for progress updates
        """
        today = datetime.now().strftime('%Y-%m-%d')

        results = {
            'updated': [],
            'failed': [],
            'skipped': []
        }

        total = len(self.all_tickers)
        print(f"Starting update for {total} tickers...")

        for idx, ticker in enumerate(self.all_tickers, 1):
            # Call progress callback if provided
            if progress_callback:
                progress_callback(idx, total, ticker)

            # Log progress every 20 tickers
            if idx % 20 == 0:
                print(f"Progress: {idx}/{total} tickers processed")

            # Determine what data to fetch
            if ticker in self.price_cache and not force_refresh:
                last_date = max(self.price_cache[ticker].keys())
                if last_date >= today:
                    results['skipped'].append(ticker)
                    continue
                # Only fetch today's price (most recent end of day)
                start_date = today
            else:
                # First time - fetch full historical data from inception
                start_date = self.inception_date

            # Fetch data
            prices = self._fetch_ticker_data(ticker, start_date, today)

            if prices:
                # Merge with existing cache
                if ticker not in self.price_cache:
                    self.price_cache[ticker] = {}
                self.price_cache[ticker].update(prices)
                results['updated'].append(ticker)
            else:
                results['failed'].append(ticker)

        # Save updated cache
        self._save_cache()

        return results

    def get_price_series(self, ticker):
        """Get price series for a ticker as pandas Series"""
        if ticker not in self.price_cache:
            return pd.Series()

        prices = self.price_cache[ticker]
        series = pd.Series(prices)
        series.index = pd.to_datetime(series.index)
        series = series.sort_index()
        return series

    def calculate_position_returns(self):
        """Calculate returns for each position (long and short)"""
        position_data = []
        inception_date = pd.to_datetime(self.inception_date)

        # Process long positions
        for ticker in self.long_tickers:
            prices = self.get_price_series(ticker)
            if len(prices) < 2:
                continue

            # Filter prices to only include data from inception date onwards
            prices = prices[prices.index >= inception_date]
            if len(prices) < 1:
                continue

            inception_price = prices.iloc[0]
            current_price = prices.iloc[-1]
            total_return = (current_price / inception_price - 1) * 100  # Long return

            position_data.append({
                'ticker': ticker,
                'side': 'Long',
                'inception_price': round(inception_price, 2),
                'current_price': round(current_price, 2),
                'total_return_pct': round(total_return, 2),
                'position_size': self.initial_capital * self.position_size,
                'current_value': round(self.initial_capital * self.position_size * (1 + total_return / 100), 2),
                'pnl': round(self.initial_capital * self.position_size * total_return / 100, 2)
            })

        # Process short positions
        for ticker in self.short_tickers:
            prices = self.get_price_series(ticker)
            if len(prices) < 2:
                continue

            # Filter prices to only include data from inception date onwards
            prices = prices[prices.index >= inception_date]
            if len(prices) < 1:
                continue

            inception_price = prices.iloc[0]
            current_price = prices.iloc[-1]
            total_return = -(current_price / inception_price - 1) * 100  # Short return (inverted)

            position_data.append({
                'ticker': ticker,
                'side': 'Short',
                'inception_price': round(inception_price, 2),
                'current_price': round(current_price, 2),
                'total_return_pct': round(total_return, 2),
                'position_size': self.initial_capital * self.position_size,
                'current_value': round(self.initial_capital * self.position_size * (1 + total_return / 100), 2),
                'pnl': round(self.initial_capital * self.position_size * total_return / 100, 2)
            })

        return position_data

    def calculate_portfolio_timeseries(self):
        """Calculate daily portfolio value and returns"""
        inception_date = pd.to_datetime(self.inception_date)

        # Get all unique dates from inception onwards
        all_dates = set()
        for ticker in self.all_tickers:
            if ticker in self.price_cache:
                all_dates.update(self.price_cache[ticker].keys())

        # Filter dates to only include inception date and after
        all_dates = sorted([d for d in all_dates if pd.to_datetime(d) >= inception_date])
        if not all_dates:
            return pd.DataFrame()

        # Build price matrix
        long_returns = []
        short_returns = []

        for date in all_dates:
            date_long_return = []
            date_short_return = []

            # Calculate long side
            for ticker in self.long_tickers:
                prices = self.get_price_series(ticker)
                # Filter to inception date onwards
                prices = prices[prices.index >= inception_date]

                if date in prices.index.strftime('%Y-%m-%d'):
                    date_idx = prices.index.get_loc(pd.to_datetime(date))
                    # Calculate return from inception (first price after inception date)
                    ret = prices.iloc[date_idx] / prices.iloc[0] - 1
                    date_long_return.append(ret)

            # Calculate short side
            for ticker in self.short_tickers:
                prices = self.get_price_series(ticker)
                # Filter to inception date onwards
                prices = prices[prices.index >= inception_date]

                if date in prices.index.strftime('%Y-%m-%d'):
                    date_idx = prices.index.get_loc(pd.to_datetime(date))
                    # Calculate return from inception (inverted for short)
                    ret = -(prices.iloc[date_idx] / prices.iloc[0] - 1)
                    date_short_return.append(ret)

            if date_long_return or date_short_return:
                long_avg = np.mean(date_long_return) if date_long_return else 0
                short_avg = np.mean(date_short_return) if date_short_return else 0
                portfolio_return = (long_avg + short_avg) / 2  # Equal weight long/short

                long_returns.append({
                    'date': date,
                    'long_return': long_avg,
                    'short_return': short_avg,
                    'portfolio_return': portfolio_return
                })

        df = pd.DataFrame(long_returns)
        if df.empty:
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Calculate cumulative returns
        df['cumulative_return'] = (1 + df['portfolio_return']).cumprod() - 1
        df['portfolio_value'] = self.initial_capital * (1 + df['cumulative_return'])

        # Add S&P 500 benchmark
        sp500_prices = self.get_price_series(self.sp500_ticker)
        if not sp500_prices.empty:
            # Filter to inception date onwards
            sp500_prices = sp500_prices[sp500_prices.index >= inception_date]
            if not sp500_prices.empty:
                sp500_returns = sp500_prices / sp500_prices.iloc[0] - 1
                df = df.join(sp500_returns.rename('sp500_return'), how='left')
                df['sp500_return'] = df['sp500_return'].fillna(method='ffill')

        # Add Russell 3000 benchmark
        russell3000_prices = self.get_price_series(self.russell3000_ticker)
        if not russell3000_prices.empty:
            # Filter to inception date onwards
            russell3000_prices = russell3000_prices[russell3000_prices.index >= inception_date]
            if not russell3000_prices.empty:
                russell3000_returns = russell3000_prices / russell3000_prices.iloc[0] - 1
                df = df.join(russell3000_returns.rename('russell3000_return'), how='left')
                df['russell3000_return'] = df['russell3000_return'].fillna(method='ffill')

        return df

    def calculate_metrics(self):
        """Calculate portfolio performance metrics"""
        timeseries = self.calculate_portfolio_timeseries()
        if timeseries.empty:
            return {}

        positions = self.calculate_position_returns()

        # Current portfolio value
        current_value = timeseries['portfolio_value'].iloc[-1]
        total_return_pct = (current_value / self.initial_capital - 1) * 100
        total_pnl = current_value - self.initial_capital

        # Long and short side P&L
        long_pnl = sum([p['pnl'] for p in positions if p['side'] == 'Long'])
        short_pnl = sum([p['pnl'] for p in positions if p['side'] == 'Short'])

        # Daily returns for volatility and Sharpe
        daily_returns = timeseries['portfolio_return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized

        # Sharpe ratio (assuming 0% risk-free rate)
        if volatility > 0:
            sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0

        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        # Best and worst positions
        sorted_positions = sorted(positions, key=lambda x: x['pnl'], reverse=True)
        best_positions = sorted_positions[:5]
        worst_positions = sorted_positions[-5:]

        # Benchmark comparison
        sp500_return = 0
        if 'sp500_return' in timeseries.columns:
            sp500_return = timeseries['sp500_return'].iloc[-1] * 100

        russell3000_return = 0
        if 'russell3000_return' in timeseries.columns:
            russell3000_return = timeseries['russell3000_return'].iloc[-1] * 100

        # Latest date
        latest_date = timeseries.index[-1].strftime('%Y-%m-%d')

        return {
            'current_value': round(current_value, 2),
            'total_return_pct': round(total_return_pct, 2),
            'total_pnl': round(total_pnl, 2),
            'long_pnl': round(long_pnl, 2),
            'short_pnl': round(short_pnl, 2),
            'volatility': round(volatility, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'best_positions': best_positions,
            'worst_positions': worst_positions,
            'sp500_return': round(sp500_return, 2),
            'russell3000_return': round(russell3000_return, 2),
            'latest_date': latest_date,
            'days_active': len(timeseries)
        }

    def get_chart_data(self):
        """Prepare data for charts"""
        timeseries = self.calculate_portfolio_timeseries()
        if timeseries.empty:
            return {}

        # Convert to list format for JavaScript
        dates = [d.strftime('%Y-%m-%d') for d in timeseries.index]
        portfolio_values = timeseries['portfolio_value'].tolist()
        portfolio_returns = (timeseries['cumulative_return'] * 100).tolist()

        # Daily returns
        daily_returns = (timeseries['portfolio_return'] * 100).tolist()

        # Drawdown
        cumulative = (1 + timeseries['portfolio_return']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = ((cumulative - running_max) / running_max * 100).tolist()

        # Benchmarks
        sp500_returns = []
        if 'sp500_return' in timeseries.columns:
            sp500_returns = (timeseries['sp500_return'] * 100).tolist()

        russell3000_returns = []
        if 'russell3000_return' in timeseries.columns:
            russell3000_returns = (timeseries['russell3000_return'] * 100).tolist()

        return {
            'dates': dates,
            'portfolio_values': portfolio_values,
            'portfolio_returns': portfolio_returns,
            'daily_returns': daily_returns,
            'drawdown': drawdown,
            'sp500_returns': sp500_returns,
            'russell3000_returns': russell3000_returns
        }
