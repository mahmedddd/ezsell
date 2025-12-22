#!/bin/bash
# EZSell Application Launcher for Linux/Mac

echo "========================================"
echo "Starting EZSell Application"
echo "========================================"
echo

# Start Backend
echo "Starting Backend Server..."
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 3

# Start Frontend
echo "Starting Frontend Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3

echo
echo "========================================"
echo "Application Started!"
echo "========================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:8080"
echo "API Docs: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop all servers..."

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'; exit" INT
wait
