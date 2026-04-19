#!/bin/bash

# GraphCortex Setup Script
# "One command to rule the swarm."

echo "Initializing GraphCortex Swarm..."

# 1. Check for .env file
if [ ! -f .env ]; then
    echo ".env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "ACTION REQUIRED: Please edit the .env file with your GEMINI_API_KEY and NEO4J credentials."
    exit 1
fi

# 2. Build and Start the services
echo "Building and starting containers (Neo4j, Ray, GraphCortex)..."
docker-compose up -d --build

# 3. Wait for Neo4j to be healthy
echo "Waiting for Neo4j to stabilize..."
until [ "$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' neo4j_nsdmg 2>/dev/null)" == "healthy" ]; do
    printf "."
    sleep 2
done

echo "✅ Swarm is running in the background!"
echo ""
echo "--------------------------------------------------------"
echo "🌐 API Swarm Endpoint (REST):"
echo "   http://localhost:8000"
echo "   Docs/Swagger: http://localhost:8000/docs"
echo ""
echo "🖥️  To interact with the CLI Swarm, run:"
echo "   docker attach graphcortex_swarm"
echo ""
echo "📊 To view the Ray Dashboard, visit:"
echo "   http://localhost:8265"
echo ""
echo "🕸️  To explore the Knowledge Graph (Neo4j Browser):"
echo "   http://localhost:7474 (Username: neo4j, Password: your_password)"
echo "--------------------------------------------------------"
