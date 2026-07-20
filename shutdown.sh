#!/bin/zsh

# GraphCortex Shutdown Script
# "Cleanly stop the swarm."

echo "Stopping GraphCortex Swarm and FalkorDB Database..."

# 1. Stop and remove containers
docker-compose down

echo ""
echo "✅ Swarm shutdown complete."
echo "   Database data is preserved in the ./data directory."
echo ""
echo "To restart, simply run: ./setup.sh"
