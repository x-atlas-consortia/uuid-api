#!/bin/bash

# Copy over the src folder
cp -r ../src uuid-api/

# Copy over the sql database
cp -r ../sql/uuids-dev.sql hubmap-mysql/uuids-dev.sql
