#!/bin/bash
cd "$(dirname "$0")"
docker-compose up -d
echo "Argus started. Frontend: http://localhost:3000 | Backend: http://localhost:8000/docs"
