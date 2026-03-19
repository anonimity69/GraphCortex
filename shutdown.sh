#!/bin/bash

# GraphCortex Shutdown Script
# "Cleanly stop the swarm."

echo "Stopping GraphCortex Swarm and Neo4j Database..."

# 1. Stop and remove containers
docker-compose down

echo ""
echo "✅ Swarm shutdown complete."
echo "   Database data is preserved in the ./data directory."
echo ""
echo "To restart, simply run: ./setup.sh"
