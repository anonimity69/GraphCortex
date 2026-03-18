#!/bin/bash

# GraphCortex Setup Script
# "One command to rule the swarm."

echo "Initializing GraphCortex Swarm (Docker + CLI)..."

# 0. Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ ERROR: Docker daemon is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# 1. Check for .env file
if [ ! -f .env ]; then
    echo ".env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "ACTION REQUIRED: Please edit the .env file with your GEMINI_API_KEY and NEO4J credentials."
    exit 1
fi

# 2. Build and Start the services
echo "Building and starting containers (Neo4j and GraphCortex Swarm)..."
if ! docker-compose up -d --build; then
    echo "❌ ERROR: Failed to start containers. Check your Docker configuration."
    exit 1
fi

# 3. Wait for Neo4j to be healthy
echo "Waiting for Neo4j to stabilize (this usually takes 30-45s)..."
MAX_RETRIES=60
RETRY_COUNT=0
BAR_SIZE=40

until [ "$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' neo4j_nsdmg 2>/dev/null)" == "healthy" ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo ""
        echo "❌ ERROR: Neo4j failed to stabilize within 2 minutes."
        echo "Check logs with: docker logs neo4j_nsdmg"
        exit 1
    fi

    # Calculate progress bar
    PROGRESS=$((RETRY_COUNT * BAR_SIZE / MAX_RETRIES))
    REMAINING=$((BAR_SIZE - PROGRESS))
    PERCENT=$((RETRY_COUNT * 100 / MAX_RETRIES))
    
    BAR=$(printf "%${PROGRESS}s" | tr ' ' '#')
    SPACE=$(printf "%${REMAINING}s" | tr ' ' '-')
    
    printf "\r[%s%s] %d%% (%ds elapsed)" "$BAR" "$SPACE" "$PERCENT" "$((RETRY_COUNT * 2))"
    
    sleep 2
done

echo -e "\n\n✅ Swarm is running in the background!"
echo ""
echo "--------------------------------------------------------"
echo "🖥️  To interact with the CLI Swarm, run:"
echo "   docker attach graphcortex_swarm"
echo ""
echo "🕸️  To explore the Knowledge Graph (Neo4j Browser):"
echo "   http://localhost:7474 (Username: neo4j, Password: your_password)"
echo "--------------------------------------------------------"
