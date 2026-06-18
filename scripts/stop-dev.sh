#!/bin/bash

# Multi-Agent Platform - Stop Script

echo "🛑 Stopping Multi-Agent Platform..."

# Stop all Docker services
docker-compose down

echo "✅ All services stopped"
echo ""
echo "Note: Data is preserved in Docker volumes"
echo "To remove all data: docker-compose down -v"
