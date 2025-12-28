#!/bin/bash

# Scotty Scheduler - Quick Run Script
# Runs both backend and frontend in the same terminal using tmux

set -e

echo "Starting Scotty Scheduler..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please run ./setup.sh first"
        exit 1
    fi
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if tmux is available
if command -v tmux &> /dev/null; then
    echo "Starting servers in tmux session 'scotty'..."
    echo ""
    echo "Commands:"
    echo "  - Ctrl+B, then 0: Switch to backend"
    echo "  - Ctrl+B, then 1: Switch to frontend"
    echo "  - Ctrl+C in each pane to stop"
    echo "  - Type 'exit' in both panes to close"
    echo ""
    sleep 2

    # Create new tmux session with two panes
    tmux new-session -d -s scotty -n "Scotty Scheduler"
    tmux send-keys -t scotty "source venv/bin/activate && python inference.py" C-m
    tmux split-window -h -t scotty
    tmux send-keys -t scotty "source venv/bin/activate && sleep 5 && streamlit run home.py" C-m
    tmux attach-session -t scotty
else
    echo "tmux not found. Starting servers in background..."
    echo ""
    echo "Starting backend..."
    python inference.py &
    BACKEND_PID=$!
    echo "Backend running with PID: $BACKEND_PID"

    sleep 5

    echo "Starting frontend..."
    streamlit run home.py &
    FRONTEND_PID=$!
    echo "Frontend running with PID: $FRONTEND_PID"

    echo ""
    echo "Both servers are running!"
    echo "Press Ctrl+C to stop both servers"

    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
fi
