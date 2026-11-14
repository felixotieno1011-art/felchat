#!/usr/bin/env bash
echo "Starting Postgres..."
sudo service postgresql start
echo "Installing and starting Redis..."
sudo apt-get install -y redis-server >/dev/null 2>&1 || true
sudo service redis-server start
echo "Starting FelChat API..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
