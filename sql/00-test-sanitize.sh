#!/bin/bash

SQL_DIR="/docker-entrypoint-initdb.d"
SQL_FILE="$SQL_DIR/uuid-api.sql"

sed -i "s/COLLATE 'Default Collation'/COLLATE utf8mb4_0900_ai_ci/g" "$SQL_FILE"
