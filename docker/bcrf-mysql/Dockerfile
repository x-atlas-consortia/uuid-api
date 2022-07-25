# Parent image
FROM mysql

LABEL description="BCRF MySQL 8.0.29 for UUID API Service" \
	version="0.1"

# Copy from host to image
COPY 01-uuid-api.forwardEngineer.sql /docker-entrypoint-initdb.d/01-uuid-api.forwardEngineer.sql
COPY 02-seed-uuids.sql /docker-entrypoint-initdb.d/02-seed-uuids.sql
COPY 03-seed-uuids-attributes.sql /docker-entrypoint-initdb.d/03-seed-uuids-attributes.sql
COPY 04-seed-organs.sql /docker-entrypoint-initdb.d/04-seed-organs.sql
COPY 05-seed-files.sql /docker-entrypoint-initdb.d/05-seed-files.sql
COPY 06-seed-data-centers.sql /docker-entrypoint-initdb.d/06-seed-data-centers.sql
COPY 07-seed-ancestors.sql /docker-entrypoint-initdb.d/07-seed-ancestors.sql
