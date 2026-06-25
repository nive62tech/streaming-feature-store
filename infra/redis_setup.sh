#!/bin/bash
echo ">>> Checking Redis connection..."
redis-cli ping

if [ $? -eq 0 ]; then
  echo ">>> Redis is running. Connection successful."
  echo ">>> Redis info:"
  redis-cli info server | grep -E "redis_version|tcp_port|uptime_in_seconds"
else
  echo ">>> Redis is NOT running. Start it with: redis-server"
fi