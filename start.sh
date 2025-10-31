#!/bin/bash
cd portfolio_simulator
gunicorn --bind 0.0.0.0:$PORT --timeout 600 --workers 1 --worker-class sync --max-requests 1000 --max-requests-jitter 50 app:app
