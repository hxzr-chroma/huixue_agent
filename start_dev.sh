#!/bin/bash
# Huixue Agent 2.0 - Development Start Script

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Start FastAPI backend (in background)
echo "Starting FastAPI backend on http://localhost:8000..."
python -m uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Streamlit frontend
echo "Starting Streamlit frontend on http://localhost:8501..."
streamlit run streamlit_app_new.py --logger.level=info

# Cleanup
trap "kill $BACKEND_PID" EXIT
