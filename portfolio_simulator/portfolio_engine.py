"""
Portfolio calculation engine for long-short equal-weight strategy
Handles price data fetching, caching, and performance metrics
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from config import TOP_100, BOTTOM_100, INITIAL_CAPITAL, INCEPTION_DATE, BENCHMARK_TICKER, POSITION_SIZE


class PortfolioEngine:
    def __init__(self, cache_dir='data'):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'price_cache.json')
        self.long_tickers = TOP_100
        self.short_tickers = BOTTOM_100
        self.all_tickers = TOP_100 + BOTTOM_100 + [BENCHMARK_TICKER]
        self.initial_capital = INITIAL_CAPITAL
        self.inception_date = INCEPTION_DATE
        self.position_size = POSITION_SIZE

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

    def _fetch_ticker_data(self, ticker, start_date, end_date):
        """Fetch historical price data for a single ticker"""
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if data.empty:
                return None

            # Convert to dictionary with date strings as keys
            prices = {}
            for date, row in data.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                prices[date_str] = float(row['Adj Close'])

            return prices
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def update_price_data(self, force_refresh=False):
        """
        Update price data for all tickers
        Only fetches new data since last update to minimize API calls
        """
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = self.inception_date

        results = {
            'updated': [],
            'failed': [],
            'skipped': []
        }

        for ticker in self.all_tickers:
            # Check if we need to update this ticker
            if ticker in self.price_cache and not force_refresh:
                last_date = max(self.price_cache[ticker].keys())
                if last_date >= today:
                    results['skipped'].append(ticker)
                    continue
                # Only fetch from last cached date
                start_date = last_date
            else:
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

        # Process long positions
        for ticker in self.long_tickers:
            prices = self.get_price_series(ticker)
            if len(prices) < 2:
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
        # Get all unique dates
        all_dates = set()
        for ticker in self.all_tickers:
            if ticker in self.price_cache:
                all_dates.update(self.price_cache[ticker].keys())

        all_dates = sorted(list(all_dates))
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
                if date in prices.index.strftime('%Y-%m-%d'):
                    date_idx = prices.index.get_loc(pd.to_datetime(date))
                    if date_idx > 0:
                        ret = prices.iloc[date_idx] / prices.iloc[0] - 1
                        date_long_return.append(ret)

            # Calculate short side
            for ticker in self.short_tickers:
                prices = self.get_price_series(ticker)
                if date in prices.index.strftime('%Y-%m-%d'):
                    date_idx = prices.index.get_loc(pd.to_datetime(date))
                    if date_idx > 0:
                        ret = -(prices.iloc[date_idx] / prices.iloc[0] - 1)  # Inverted for short
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
            return df

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Calculate cumulative returns
        df['cumulative_return'] = (1 + df['portfolio_return']).cumprod() - 1
        df['portfolio_value'] = self.initial_capital * (1 + df['cumulative_return'])

        # Add benchmark
        benchmark_prices = self.get_price_series(BENCHMARK_TICKER)
        if not benchmark_prices.empty:
            benchmark_returns = benchmark_prices / benchmark_prices.iloc[0] - 1
            df = df.join(benchmark_returns.rename('benchmark_return'), how='left')
            df['benchmark_return'] = df['benchmark_return'].fillna(method='ffill')

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
        benchmark_return = 0
        if 'benchmark_return' in timeseries.columns:
            benchmark_return = timeseries['benchmark_return'].iloc[-1] * 100

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
            'benchmark_return': round(benchmark_return, 2),
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

        # Benchmark
        benchmark_returns = []
        if 'benchmark_return' in timeseries.columns:
            benchmark_returns = (timeseries['benchmark_return'] * 100).tolist()

        return {
            'dates': dates,
            'portfolio_values': portfolio_values,
            'portfolio_returns': portfolio_returns,
            'daily_returns': daily_returns,
            'drawdown': drawdown,
            'benchmark_returns': benchmark_returns
        }
