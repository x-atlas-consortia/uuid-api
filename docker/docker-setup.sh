#!/bin/bash

# Set the version environment variable for the docker build
# Version number is from the VERSION file
# Also remove newlines and leading/trailing slashes if present in that VERSION file
export UUID_API_VERSION=$(tr -d "\n\r" < ../VERSION | xargs)
echo "UUID_API_VERSION: $UUID_API_VERSION"

# Copy over the src folder
cp -r ../src uuid-api/
# Copy over the sql database
cp -r ../sql/uuids-dev.sql hubmap-mysql/uuids-dev.sql
