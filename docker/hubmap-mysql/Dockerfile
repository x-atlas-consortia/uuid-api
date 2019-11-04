# Parent image
FROM mysql:5.6

LABEL description="HuBMAP MySQL 5.6 for UUID API Service" \
	version="1.1"

# Copy from host to image
COPY ./uuids-dev.sql /docker-entrypoint-initdb.d/uuids-dev.sql
