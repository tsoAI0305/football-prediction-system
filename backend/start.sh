#!/bin/bash
# Quick start script for Football Prediction System

set -e

echo "🚀 Starting Football Prediction System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env to add your API keys if needed"
    echo ""
fi

# Start services
echo "🐳 Starting Docker containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."
docker compose ps

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Access points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Useful commands:"
echo "   - View logs: docker compose logs -f api"
echo "   - Stop services: docker compose down"
echo "   - Restart: docker compose restart"
echo ""
echo "💡 To populate sample data, run:"
echo "   docker compose exec api python create_sample_data.py"
echo ""
