#!/bin/bash
# Run Nuze in development mode
# Frontend: Vite dev server with hot reload (port 5174)
# Backend: FastAPI (port 8000)

echo "🔧 Starting Nuze in DEVELOPMENT mode..."
echo "🔨 Building frontend with dev configuration..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo ""
echo "✅ Services started:"
echo "   Frontend: http://localhost:5174 (hot reload enabled)"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To view logs: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "🛑 To stop: docker compose -f docker-compose.yml -f docker-compose.dev.yml down"
