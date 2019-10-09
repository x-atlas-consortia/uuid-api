# uuid-api for HuBMAP
The uuid-api service is a restful web service used to create and query UUIDs used across HuBMAP.

## Local development

### Flask config

This application is written in Flask and it includes `uuid.properties.example` and `uuid_app.conf.example` in the `/conf` directory.  Copy the files and remove the `.example` from filename then modify with the appropriate information.

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

## Local testing against HuBMAP Gateway

For running the uuid-api service behind the gateway, we'll build docker images for each project and set up the configurations.

This also requires to have the [HuBMAP Gateway](https://github.com/hubmapconsortium/gateway) running locally because it creates the network for communication between these two docker-compose projects.

### Overview of tools

- [Docker](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

Note: Docker Compose requires Docker to be installed and running first.


### uWSGI config

In the `Dockerfile`, we installed uWSGI and the uWSGI Python plugin via yum. There's also a uWSGI configuration file at `src/uwsgi.ini` and it tells uWSGI the details of running this Flask app.


### Build docker image

````
sudo docker-compose build
````

### Start up service

````
sudo docker-compose up
````