# Portfolio Simulator - Quick Start Guide

## First Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` and add your Marketstack API key:
```
MARKETSTACK_API_KEY=your_actual_api_key_here
```

Get your API key from: https://marketstack.com/dashboard

### 3. Run the Application

#### Option A: Easy Reset & Run (Recommended for first time)
**Windows:**
```bash
reset_and_run.bat
```

**Mac/Linux:**
```bash
chmod +x reset_and_run.sh
./reset_and_run.sh
```

#### Option B: Manual Run
```bash
python app.py
```

### 4. Access the Dashboard
1. Open browser to: http://127.0.0.1:5000
2. **Hard refresh** the page (Ctrl+F5 or Cmd+Shift+R)
3. Wait for initial data load (3-5 minutes for 202 tickers)

---

## Troubleshooting

### Issue: Old UI showing "Massive.com" or refresh button
**Solution:**
1. Stop the Flask server (Ctrl+C)
2. Restart: `python app.py`
3. Hard refresh browser (Ctrl+F5)

### Issue: Benchmark returns showing 0%
**Solution:**
1. Delete old cache: `rm data/price_cache.json` (Mac/Linux) or `del data\price_cache.json` (Windows)
2. Restart application: `python app.py`
3. Wait for fresh data to load

### Issue: "No data available"
**Solution:**
1. Check your `.env` file has valid Marketstack API key
2. Verify API key works: https://marketstack.com/dashboard
3. Check console for error messages

### Issue: API rate limit errors
**Solution:**
- Basic plan: 10,000 requests/month
- Daily updates use ~202 requests
- If exceeded, wait until next month or upgrade plan

---

## Features

### Automated Updates
- **Schedule**: Daily at 10:00 PM EST
- **No manual intervention needed**
- Status displayed in header

### Data Source
- **Provider**: Marketstack.com
- **Plan**: Basic (10,000 requests/month)
- **Coverage**: 200 tickers + 2 benchmarks

### Inception Date
- **Start**: October 28th, 2025
- All returns calculated from end-of-day prices on this date

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review console logs for error messages
- Verify `.env` configuration
- Ensure dependencies are installed correctly
