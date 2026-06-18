#!/bin/bash
set -e

echo "Initializing PostgreSQL extensions..."

# Create extensions in the multiagent database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Core extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
    
    -- pgvector (if available)
    DO \$\$
    BEGIN
        CREATE EXTENSION IF NOT EXISTS "vector";
        RAISE NOTICE 'pgvector extension created successfully';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'pgvector extension not available, continuing without it';
    END
    \$\$;
    
    -- Show installed extensions
    SELECT extname, extversion FROM pg_extension ORDER BY extname;
EOSQL

echo "Extensions initialized successfully!"
