#!/bin/sh

# Start FastAPI backend on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Use Hugging Face PORT or default to 7860 (their default for Gradio-like apps)
PORT=${PORT:-7860}

# Start Streamlit **on required $PORT**
streamlit run streamlit_app/app.py --server.port "$PORT" --server.address 0.0.0.0
