#!/bin/bash

# Set the version environment variable for the docker build
# Version number is from the VERSION file
export UUID_API_VERSION=`cat VERSION`

echo "UUID_API_VERSION: $UUID_API_VERSION"

# Copy over the src folder
cp -r ../src uuid-api/

# Copy over the sql database
cp -r ../sql/uuids-dev.sql hubmap-mysql/uuids-dev.sql
