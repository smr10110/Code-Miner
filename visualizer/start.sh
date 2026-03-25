#!/bin/bash
# Launch FastAPI in background
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to be ready
sleep 2

# Launch Streamlit in foreground
streamlit run dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
