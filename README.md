# uuid-api for HuBMAP
The uuid-api service is a restful web service used to create and query UUIDs used across HuBMAP.

## Local development

### Flask app configuration

This application is written in Flask and it includes `app.cfg.example` in the `/src/instance` directory.  Copy the file and remove the `.example` from filename then modify with the appropriate information.

### Install dependencies

````
sudo pip3 install -r src/requirements.txt
````

Note: if you need to use a modified version of the [HuBMAP commons] dependency, download the code and make changes, then install the dependency using `src/requirements_dev.txt` and make sure the local file system path is specified correctly.

### Start Flask development server

````
cd src
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
````

This code runs by default on port 5000. You can change the port using a `-p` or `--port` switch at command line. For instance:

````
flask run -p 5001
````

## Local testing against HuBMAP Gateway in a containerized environment

This option allows you to setup all the pieces (gateway for authentication, MySQL database server...) in a containerized environment with docker and docker-compose. This requires to have the [HuBMAP Gateway](https://github.com/hubmapconsortium/gateway) running locally.

### Required tools

- [Docker](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Note: Docker Compose requires Docker to be installed and running first.


### uWSGI config

In the `Dockerfile`, we installed uWSGI and the uWSGI Python plugin via yum. There's also a uWSGI configuration file at `src/uwsgi.ini` and it tells uWSGI the details of running this Flask app.


### Build docker image

````
cd docker
./docker-setup.sh
sudo docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
````

### Start up container

````
sudo docker-compose -p uuid-api_and_mysql -f docker-compose.yml -f docker-compose.dev.yml up -d
````

Note: here we specify the docker compose project with the `-p` to avoid "WARNING: Found orphan containers ..." due to the fact that docker compose uses the directory name as the default project name.

### Shell into the MySQL container to load the database table sql

````
sudo docker exec -it <mysql container ID> bash
````

Inside the MySQL container:

````
cd /usr/src/uuid-api/sql
````

Import the `hm_uuids` table into the database:

````
root@hubmap-mysql:/usr/src/uuid-api/sql# mysql -u root -p hm_uuid < uuids-dev.sql
````

Note: the MySQL username and password are specified in the docker-compose yaml file.