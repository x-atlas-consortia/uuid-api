# Parent image
FROM mysql

LABEL description="BCRF MySQL 8.0.29 for UUID API Service" \
	version="0.1"

# Copy from host to image
COPY ./uuid-api.forwardEngineer.sql /docker-entrypoint-initdb.d/uuid-api.forwardEngineer.sql
