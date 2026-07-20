#!/bin/zsh

# GraphCortex Setup Script
# "One command to rule the swarm."

echo "Initializing GraphCortex Swarm (Docker + CLI)..."

# 0. Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ ERROR: Docker daemon is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# 0.1 Check for port conflicts (6379, 3000)
for port in 6379 3000; do
    PID=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ ! -z "$PID" ]; then
        # If the port is in use, check if it's by our own Docker container
        CONF_OWNER=$(docker ps --filter "name=falkordb_graphcortex" --format "{{.Names}}" 2>/dev/null)
        if [[ "$CONF_OWNER" != "falkordb_graphcortex" ]]; then
            echo "❌ ERROR: Port $port is already in use by another process."
            echo "Please stop any other services using this port."
            lsof -i :$port
            exit 1
        fi
    fi
done

# 1. Check for .env file
if [ ! -f .env ]; then
    echo ".env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "ACTION REQUIRED: Please edit the .env file with your GEMINI_API_KEY."
    exit 1
fi

# 2. Build and Start the services
echo "Building and starting containers (FalkorDB and GraphCortex Swarm)..."
if ! docker-compose up -d --build; then
    echo "❌ ERROR: Failed to start containers. Check your Docker configuration."
    exit 1
fi

# 3. Wait for FalkorDB to be healthy
echo "Waiting for FalkorDB to stabilize..."
MAX_RETRIES=30
RETRY_COUNT=0
BAR_SIZE=40

until [ "$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' falkordb_graphcortex 2>/dev/null)" == "healthy" ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo ""
        echo "❌ ERROR: FalkorDB failed to stabilize within 30 seconds."
        echo "Check logs with: docker logs falkordb_graphcortex"
        exit 1
    fi

    # Calculate progress bar
    PROGRESS=$((RETRY_COUNT * BAR_SIZE / MAX_RETRIES))
    REMAINING=$((BAR_SIZE - PROGRESS))
    PERCENT=$((RETRY_COUNT * 100 / MAX_RETRIES))
    
    BAR=$(printf "%${PROGRESS}s" | tr ' ' '#')
    SPACE=$(printf "%${REMAINING}s" | tr ' ' '-')
    
    printf "\r[%s%s] %d%% (%ds elapsed)" "$BAR" "$SPACE" "$PERCENT" "$((RETRY_COUNT * 1))"
    
    sleep 1
done

echo ""
echo "✅ Swarm is online!"
echo "--------------------------------------------------------"
echo "🕸️  Knowledge Graph (FalkorDB Browser): http://localhost:3000"
echo "--------------------------------------------------------"
echo ""
echo "Entering Swarm CLI..."
echo "(Press Ctrl+C to shutdown the swarm)"
echo ""

# Auto-attach to the CLI
docker attach graphcortex_swarm
