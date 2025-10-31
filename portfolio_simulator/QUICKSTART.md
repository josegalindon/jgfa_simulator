# Quick Start Guide

Get your portfolio simulator running in 3 simple steps!

## Windows Users

### Option 1: Use the Run Script (Easiest)
1. Double-click `run.bat`
2. Wait for dependencies to install (first time only)
3. Open browser to http://127.0.0.1:5000

### Option 2: Manual Setup
```cmd
pip install -r requirements.txt
python app.py
```

## Mac/Linux Users

### Option 1: Use the Run Script
```bash
chmod +x run.sh
./run.sh
```

### Option 2: Manual Setup
```bash
pip3 install -r requirements.txt
python3 app.py
```

## What Happens on First Run?

1. **Installation** (~1 minute)
   - Installs Flask, yfinance, pandas, numpy

2. **Data Fetching** (~5-10 minutes)
   - Downloads historical prices for 200 stocks
   - Fetches data from January 2, 2024 to today
   - Caches data locally for fast future access

3. **Server Start**
   - Flask server starts on port 5000
   - Dashboard becomes accessible in browser

## Accessing the Dashboard

Once you see "Running on http://127.0.0.1:5000", open your browser and navigate to:

**Local access:**
```
http://127.0.0.1:5000
```

**From other devices on same network:**
```
http://YOUR_IP_ADDRESS:5000
```

Find your IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `ip addr`

## First-Time Checklist

- [ ] Python 3.8+ installed
- [ ] Internet connection active
- [ ] Port 5000 available
- [ ] Run the application
- [ ] Wait for data download (shows progress in terminal)
- [ ] Open browser to dashboard
- [ ] See your portfolio metrics!

## Refreshing Data

- Click the **"Refresh Data"** button in the dashboard
- Or restart the application
- Subsequent refreshes are much faster (only fetches new data)

## Troubleshooting

**"Python is not installed"**
- Download from https://python.org
- Make sure to check "Add to PATH" during installation

**"Module not found"**
- Run: `pip install -r requirements.txt`

**"Address already in use"**
- Another app is using port 5000
- Close other apps or change port in app.py

**Dashboard shows no data**
- Check terminal for error messages
- Verify internet connection
- Wait for initial data download to complete

## Next Steps

Once running, explore:
1. Summary metrics cards
2. Performance charts
3. Position tables (long/short tabs)
4. Best/worst performers
5. Benchmark comparison vs S&P 500

For detailed documentation, see `README.md`

---

**Need help?** Check the console output for detailed error messages.
