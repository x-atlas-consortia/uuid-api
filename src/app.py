import sys
import os
from pathlib import Path
import time
import logging
from uuid_worker import UUIDWorker
import json
from flask import Flask, request, Response, jsonify

# HuBMAP commons
from hubmap_commons.hm_auth import secured
from hubmap_commons.string_helper import isBlank


# Specify the absolute path of the instance folder and use the config file relative to the instance path
app = Flask(__name__, instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'), instance_relative_config=True)
app.config.from_pyfile('app.cfg')

LOG_FILE_NAME = "../log/uuid-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".log" 
logger = None
worker = None

@app.before_first_request
def init():
    global logger
    global worker
    try:
        logger = logging.getLogger('uuid.service')
        logger.setLevel(logging.INFO)
        logFH = logging.FileHandler(LOG_FILE_NAME)
        logger.addHandler(logFH)
        logger.info("started")
    except Exception as e:
        print("Error opening log file during startup")
        print(str(e))

    try:        
        if 'APP_CLIENT_ID' not in app.config or isBlank(app.config['APP_CLIENT_ID']):
            raise Exception("Required configuration parameter APP_CLIENT_ID not found in application configuration.")
        if 'APP_CLIENT_SECRET' not in app.config or isBlank(app.config['APP_CLIENT_ID']):
            raise Exception("Required configuration parameter APP_CLIENT_SECRET not found in application configuration.")
        cId = app.config['APP_CLIENT_ID']
        cSecret = app.config['APP_CLIENT_SECRET']
        dbHost = app.config['DB_HOST']
        dbName = app.config['DB_NAME']
        dbUsername = app.config['DB_USERNAME']
        dbPassword = app.config['DB_PASSWORD']
        worker = UUIDWorker(clientId=cId, clientSecret=cSecret, dbHost=dbHost, dbName=dbName, dbUsername=dbUsername, dbPassword=dbPassword)
        logger.info("initialized")

    except Exception as e:
        print("Error during startup.")
        print(str(e))
        logger.error(e, exc_info=True)
        print("Check the log file for further information: " + LOG_FILE_NAME)



@app.route('/', methods = ['GET'])
def index():
    return "Hello! This is HuBMAP UUID API service :)"

# Status of MySQL connection
@app.route('/status', methods=['GET'])
def status():
    global worker
    global logger

    response_data = {
        # Use strip() to remove leading and trailing spaces, newlines, and tabs
        'version': (Path(__file__).parent / 'VERSION').read_text().strip(),
        'build': (Path(__file__).parent / 'BUILD').read_text().strip(),
        'mysql_connection': False
    }

    dbcheck = worker.testConnection()
    if dbcheck:
        response_data['mysql_connection'] = True
   
    return jsonify(response_data)


'''
POST arguments in json
  entity_type- required: the type of entity, DONOR, SAMPLE, DATASET
   parent_ids- required for entity types of SAMPLE, DONOR and DATASET
               an array of UUIDs for the ancestors of the new entity
               For SAMPLEs and DONORs a single uuid is required (one entry in the array)
               and multiple ids are not allowed (SAMPLEs and DONORs are required to 
               have a single ancestor, not multiple).  For DATASETs at least one ancestor
               UUID is required, but multiple can be specified. (A DATASET can be derived
               from multiple SAMPLEs or DATASETs.) 
     organ_id- required only in the case where an id is being generated for a SAMPLE that
               has a DONOR as a direct ancestor.  Must be one of the codes from:
               https://github.com/hubmapconsortium/search-api/blob/test-release/src/search-schema/data/definitions/enums/organ_types.yaml
                 
 Query (in url) argument
   entity_count optional, the number of ids to generate.  If omitted,
                defaults to 1 
              
    For 
    
 REMOVED: generateDOI- optional, defaults to false
          submission_ids- optional, an array of ids to associate and store with the
            generated ids. If provide, the length of this array must
            match the entity_count argument
      
 curl example:  curl -d '{"entityType":"BILL-TEST","generateDOI":"true","hubmap-ids":["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]   }' -H "Content-Type: application/json" -H "Authorization: Bearer AgX07PVbz9Wb6WDK3QvP9p23j2vWV7bYnMGBvaQxQQGEY5MjJEIwC8x3vwqYmzwEzPw93qWYeGpEkKu4nOkPgs7VKQ" -X POST http://localhost:5000/hmuuid?entity_count=7  
'''
@app.route('/hmuuid', methods=["POST"])
@secured(groups="HuBMAP-read")
def add_hmuuid():
    global worker
    global logger
    try:
        if request.method == "POST":
            if 'entity_count' in request.args:
                nArgs = request.args.get('entity_count')
                if isBlank(nArgs) or not nArgs.strip().isnumeric():
                    return Response("Sample count must be an integer ", 400)
                rjson = worker.uuidPost(request, int(nArgs))
            else:
                rjson = worker.uuidPost(request, 1)
            if isinstance(rjson, Response):
                return rjson                
            #jsonStr = json.dumps(rjson)
            
            return Response(rjson, 200, {'Content-Type': "application/json"})
        else:
            return Response("Invalid request.  Use POST to create a UUID", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return(Response("Unexpected error: " + eMsg, 500))

@app.route('/hmuuid/<hmuuid>', methods=["GET"])
@secured(groups="HuBMAP-read")
def get_hmuuid(hmuuid):
    global worker
    global logger
    try:
        if request.method == "GET":
            info = worker.getIdInfo(hmuuid)
            return info
        else:
            return Response ("Invalid request use GET to retrieve UUID information", 500)
    except Exception as e:                                                                                                            
        eMsg = str(e)                                                                                                                 
        logger.error(e, exc_info=True)                                                                                                
        return(Response("Unexpected error: " + eMsg, 500))    

'''
Update id records to include display ids 

PUT arguments in json
   hubmap-uuids- an array of uuids to update
    display-ids- an array of display ids to update for the associated (same order)
                 records of the uuids passed in the hubmap-uuids array.

   Only id records that currently DO NOT have an associated display-id can be updated.
   
 curl example:  curl -d '{"hubmap-uuids":["32ae6d81bc9df2d62a550c62c02df39a", "3a2bdd52946a14081d448261c7b52bb2"], "display-ids"["lab-id-1","lab-id-2"] }' -H "Content-Type: application/json" -H "Authorization: Bearer AgX07PVbz9Wb6WDK3QvP9p23j2vWV7bYnMGBvaQxQQGEY5MjJEIwC8x3vwqYmzwEzPw93qWYeGpEkKu4nOkPgs7VKQ" -X PUT http://localhost:5000/hmuuid  
'''
'''
@app.route('/hmuuid', methods=["PUT"])
@secured(groups="HuBMAP-read")
def update_hmuuid():
    global worker
    global logger
    try:
        if request.method == "PUT":
            rjson = worker.uuidPut(request)
            if isinstance(rjson, Response):
                return rjson                
            
            return Response(rjson, 200, {'Content-Type': "application/json"})
        else:
            return Response("Invalid request.  Use PUT to update a UUID", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return(Response("Unexpected error: " + eMsg, 500))
'''

@app.route('/hmuuid/<hmuuid>/exists', methods=["GET"])
@secured(groups="HuBMAP-read")
def is_hmuuid(hmuuid):
    global worker
    global logger
    try:
        if request.method == "GET":
            exists = worker.getIdExists(hmuuid)
            if isinstance(exists, Response):
                return exists
            return json.dumps(exists)
        else:
            return Response ("Invalid request use GET to check the status of a UUID", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return(Response("Unexpected error: " + eMsg, 500))


    
if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port="5001")
    except Exception as e:
        print("Error during starting debug server.")
        print(str(e))
        logger.error(e, exc_info=True)
        print("Check the log file for further information: " + LOG_FILE_NAME)

