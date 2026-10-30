#!/usr/bin/env bash
# Idempotent Postgres setup for FelChat on a Codespaces default container.
# Run: bash scripts/setup_db.sh
set -e

sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib postgresql-16-pgvector

sudo service postgresql start
sleep 1

cat > /tmp/init_felchat.sql << 'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'felchat') THEN
    CREATE ROLE felchat LOGIN PASSWORD 'felchat';
  END IF;
END
$$;
SQL

sudo cp /tmp/init_felchat.sql /var/lib/postgresql/init_felchat.sql
sudo chown postgres:postgres /var/lib/postgresql/init_felchat.sql
sudo su - postgres -c "psql -v ON_ERROR_STOP=1 -f /var/lib/postgresql/init_felchat.sql"
sudo rm -f /var/lib/postgresql/init_felchat.sql /tmp/init_felchat.sql

sudo su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='felchat'\"" | grep -q 1 \
  || sudo su - postgres -c "createdb -O felchat felchat"

sudo su - postgres -c "psql -d felchat -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

echo "FelChat database ready on localhost:5432 (user=felchat, db=felchat)"
