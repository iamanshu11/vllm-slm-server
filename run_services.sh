#!/bin/bash

# Function to kill child processes on exit
trap 'kill $(jobs -p)' EXIT

# Set VLLM environment variables (preserved from original code)
export VLLM_USE_V1=0

# Set PYTHONPATH to current directory so 'app' module can be found
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Define python and streamlit paths from venv
VENV_PYTHON="./.venv/bin/python"
VENV_STREAMLIT="./.venv/bin/streamlit"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at ./.venv"
    echo "Please make sure you have created a virtual environment and installed dependencies."
    exit 1
fi

echo "Starting vLLM Engine (Port 8081)..."
$VENV_PYTHON -m uvicorn app.services.llm_engine:app --host 0.0.0.0 --port 8081 &
PID_ENGINE=$!

echo "Waiting for Engine to initialize..."
sleep 5

echo "Starting API Gateway (Port 8080)..."
$VENV_PYTHON -m uvicorn app.services.api_gateway:app --host 0.0.0.0 --port 8080 &
PID_GATEWAY=$!

echo "Starting Streamlit UI..."
$VENV_STREAMLIT run app/ui/streamlit_app.py &
PID_UI=$!

echo "Services running. Press Ctrl+C to stop."
echo "Engine PID: $PID_ENGINE"
echo "Gateway PID: $PID_GATEWAY"
echo "UI PID: $PID_UI"

wait
