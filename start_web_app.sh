#!/bin/bash
# start_web_app.sh

# Ensure redis is running
redis-cli ping || redis-server --daemonize yes

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server in background
nohup uvicorn api:app --host 0.0.0.0 --port 8080 > api.log 2>&1 &

# Start Celery worker in background
nohup celery -A tasks worker --loglevel=info > celery.log 2>&1 &

# Start static file server (for output directory)
cd output
nohup python3 -m http.server 8000 --bind 0.0.0.0 > ../http.log 2>&1 &

echo "Web App started!"
echo "API Server: http://localhost:8080"
echo "Web Portal: http://localhost:8000"
