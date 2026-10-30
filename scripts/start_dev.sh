#!/usr/bin/env bash
echo "Waking up Postgres..."
sudo service postgresql start

echo "Waking up Redis..."
sudo service redis-server start

echo "Starting FelChat API..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
