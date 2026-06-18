# Custom PostgreSQL Image with Extensions
# Based on official PostgreSQL 15 Alpine

FROM postgres:15-alpine

# Install additional packages and extensions
RUN apk add --no-cache \
    # Build dependencies
    build-base \
    git \
    # PostgreSQL development files
    postgresql-dev \
    # Python (for some extensions)
    python3 \
    python3-dev

# Install pgvector extension (for embeddings/RAG)
# Note: This requires compilation which may fail on some systems
# If compilation fails, the system will work without vector support
RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install || echo "pgvector installation failed, continuing without it" && \
    cd / && \
    rm -rf /tmp/pgvector

# Install pg_stat_statements (query performance monitoring)
# Already included in PostgreSQL, just needs to be enabled

# Install pg_trgm (fuzzy text search)
# Already included in PostgreSQL, just needs to be enabled

# Set default database and user
ENV POSTGRES_DB=multiagent
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=password

# Copy custom configuration (optional)
# COPY postgresql.conf /etc/postgresql/postgresql.conf

# Copy initialization scripts
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Use official entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
