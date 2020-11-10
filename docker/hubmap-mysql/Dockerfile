# Parent image
FROM mysql:5.6

LABEL description="HuBMAP MySQL 5.6 for UUID API Service" \
	version="1.1"

# Copy from host to image
COPY ./uuids.sql /docker-entrypoint-initdb.d/uuids.sql
