#!/bin/bash

echo "🚀 Starting SmartLedger AI..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

mkdir -p logs

docker-compose up -d

echo "⏳ Waiting for services..."
sleep 10

docker-compose ps

echo ""
echo "✅ Services started!"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost"
echo "  - MinIO: http://localhost:9001"
