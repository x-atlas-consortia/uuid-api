# check if the mysql-test docker container is running and stop it
if [ "$(docker ps -q -f name=mysql-test)" ]; then
    echo "Stopping the existing mysql-test container"
    docker stop mysql-test > /dev/null
fi

# check if the mysql-test docker container exists and remove it
if [ "$(docker ps -aq -f name=mysql-test)" ]; then
    echo "Removing the existing mysql-test container"
    docker rm mysql-test > /dev/null
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# Backup the app.cfg file
CFG_BAK=false
if [ -f "$SCRIPT_DIR/src/instance/app.cfg" ]; then
    CFG_BAK=true
    cp "$SCRIPT_DIR/src/instance/app.cfg" "$SCRIPT_DIR/src/instance/app.cfg.bak"
fi
cp "$SCRIPT_DIR/tests/config/app.test.cfg" "$SCRIPT_DIR/src/instance/app.cfg"

cp "$SCRIPT_DIR/sql/uuid-api.sql" "$SCRIPT_DIR/sql/uuid-api.sql.bak"

# Create a new mysql-test docker container
echo "Creating a new mysql-test container"
docker run -d --name mysql-test \
  -p 3306:3306 \
  -e MYSQL_DATABASE=sn_uuid \
  -e MYSQL_USER=uuid_user \
  -e MYSQL_PASSWORD=uuid_password \
  -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
  -v $SCRIPT_DIR/sql:/docker-entrypoint-initdb.d \
  -v $SCRIPT_DIR/tests/config:/etc/mysql:ro \
  mysql:8.0-debian

echo "Running tests"
pytest

# Restore the app.cfg file if needed
if [ "$CFG_BAK" = true ]; then
    mv "$SCRIPT_DIR/src/instance/app.cfg.bak" "$SCRIPT_DIR/src/instance/app.cfg"
fi
mv "$SCRIPT_DIR/sql/uuid-api.sql.bak" "$SCRIPT_DIR/sql/uuid-api.sql"

echo "Stopping and removing the mysql-test container"
docker stop mysql-test > /dev/null
docker rm --volumes mysql-test > /dev/null
