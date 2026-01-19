#!/bin/bash

# Script to run FastAPI backend and Streamlit frontend

echo "🚀 Starting E-commerce Chatbot Application..."
echo ""

# Create history directory if it doesn't exist
mkdir -p history

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo "📡 Starting FastAPI backend on http://localhost:8000..."
python app.py &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 3

# Check if FastAPI started successfully
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "❌ Failed to start FastAPI backend"
    exit 1
fi

echo "✅ FastAPI backend started successfully"
echo ""

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on http://localhost:8501..."
streamlit run streamlit_app.py &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 3

# Check if Streamlit started successfully
if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "❌ Failed to start Streamlit frontend"
    kill $FASTAPI_PID 2>/dev/null
    exit 1
fi

echo "✅ Streamlit frontend started successfully"
echo ""
echo "=============================================="
echo "🎉 Application is ready!"
echo "=============================================="
echo "📡 FastAPI:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo "🎨 Streamlit: http://localhost:8501"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $FASTAPI_PID $STREAMLIT_PID
