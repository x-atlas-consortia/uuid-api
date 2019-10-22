#!/bin/bash

# Copy over the src and conf folders
cp -r ../src uuid-api/
cp -r ../conf uuid-api/

# Create log folder
mkdir uuid-api/log