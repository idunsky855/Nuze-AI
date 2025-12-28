#!/bin/bash
# Run Nuze in production mode
# Frontend: Nginx serving static build (port 5173)
# Backend: FastAPI (port 8000)

echo "🚀 Starting Nuze in PRODUCTION mode..."
echo "🔨 Building frontend with production API..."
docker compose build frontend
docker compose up -d

echo ""
echo "✅ Services started:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To view logs: docker compose logs -f"
echo "🛑 To stop: docker compose down"
