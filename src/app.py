import os
from pathlib import Path
import time
import logging
from uuid_worker import UUIDWorker
import json
from flask import Flask, request, Response, jsonify

# HuBMAP commons
# from hm_auth import secured
from hubmap_commons.hm_auth import secured
from hubmap_commons.string_helper import isBlank

# Root logger configuration
global logger

# Set logging format and level (default is warning)
# All the API logging is forwarded to the uWSGI server and gets written into the log file `log/uwsgi-uuid-api.log`
# Log rotation is handled via logrotate on the host system with a configuration file
# Do NOT handle log file and rotation via the Python logging to avoid issues with multi-worker processes
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

# Use `getLogger()` instead of `getLogger(__name__)` to apply the config to the root logger
# will be inherited by the sub-module loggers
try:
    logger = logging.getLogger()
    logger.info(f"Starting. Logger initialized, with logging level {logger.level}")
except Exception as e:
    print("Error opening log file during startup")
    print(str(e))

# Specify the absolute path of the instance folder and use the config file relative to the instance path
app = Flask(__name__, instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'),
            instance_relative_config=True)

# Use configuration from instance/app.cfg, deployed per-app from examples in the repository.
try:
    app.config.from_pyfile('app.cfg')
    logger.info("Application initialized from instance/app.cfg")
except Exception as e:
    logger.critical(f"Unable to initialize application from instance/app.cfg due to e='{str(e)}'")
    raise Exception("Failed to get configuration from instance/app.cfg")

worker = None
try:
    worker = UUIDWorker(app_config=app.config)
    logger.info("UUIDWorker instantiated using app.cfg setting.")
except Exception as e:
    logger.critical(f"Unable to instantiate a UUIDWorker during startup.")
    print("Error instantiating a UUIDWorker during startup.")
    print(str(e))
    logger.error(e, exc_info=True)
    print("Check the log file for further information: " + LOG_FILE_NAME)

logger.info('')
logger.info('')

@app.route('/', methods=['GET'])
def index():
    return "Hello! This is the UUID API service :)"


# Status of MySQL connection
@app.route('/status', methods=['GET'])
def status():
    global worker

    try:
        file_build_content = (Path(__file__).absolute().parent.parent / 'BUILD').read_text().strip()
    except Exception as e:
        file_build_content = str(e)

    response_data = {
        # Use strip() to remove leading and trailing spaces, newlines, and tabs
        'version': (Path(__file__).absolute().parent.parent / 'VERSION').read_text().strip(),
        'build': file_build_content,
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
   organ_code- required only in the case where an id is being generated for a SAMPLE that
               has a DONOR as a direct ancestor.  Must be one of the codes from:
               https://github.com/hubmapconsortium/search-api/blob/test-release/src/search-schema/data/definitions/enums/organ_types.yaml
   file_info-  required only if the entity type is FILE. A list/array of information about each
               file that requires an id to be generated for it. The size of this array is required
               to match the optional URL argument,  entity_count (or be 1 in the case where this argument
               is defaulted to 1). N.B. the field checksum has been deprecated and should be replaced
               by md5_checksum or sha256_checksum.  Requests which try to save to checksum will now fail.
               Each file info element should contain:
                     path- required: the path to the file in storage.  For the purposes of the
                                     UUID system this can be a full path or relative, but it is
                                     recommended that a relative path be used.
                                     The path attribute can contain an optional "<uuid>" tag, which
                                     will be replaced by the generated file uuid before being stored.
                                     This is useful in the case where the path to the file will include
                                     the file uuid, such as for files uploaded via the ingest portal.
                     base_dir- required: a specifier for the base directory where the file is stored
                                         valid values are: DATA_UPLOAD or INGEST_PORTAL_UPLOAD
                                        
                     md5_checksum- optional: An MD5 checksum/hash of the file
                     sha256_checksum- optional: An SHA-256 checksum/hash of the file
                     size- optional: The size of the file as an integer
   

                 
 Query (in url) argument
   entity_count optional, the number of ids to generate.  If omitted,
                defaults to 1 
              
    
 REMOVED: generateDOI- optional, defaults to false
          submission_ids- optional, an array of ids to associate and store with the
            generated ids. If provide, the length of this array must
            match the entity_count argument
      
'''
# Add backwards compatibility for older version of entity-api
@app.route('/hmuuid', methods=["POST"])
@app.route('/uuid', methods=["POST"])
@secured(has_write=True)
def add_uuid():
    global worker

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
                # jsonStr = json.dumps(rjson)

            return Response(rjson, 200, {'Content-Type': "application/json"})
        else:
            return Response("Invalid request.  Use POST to create a UUID", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


@app.route('/hmuuid/<uuid>', methods=["GET"])
@app.route('/uuid/<uuid>', methods=["GET"])
def get_uuid(uuid):
    global worker

    try:
        if request.method == "GET":
            # The info is a pretty print json string
            info = worker.getIdInfo(uuid)

            # if getIdInfo returns a Response, it is sending an error back
            if isinstance(info, Response):
                return info

            # Add the json MIME header in response
            return Response(response=info, mimetype="application/json")
        else:
            return Response("Invalid request use GET to retrieve UUID information", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


@app.route('/hmuuid/<uuid>/exists', methods=["GET"])
@app.route('/uuid/<uuid>/exists', methods=["GET"])
@secured(has_read=True)
def is_uuid(uuid):
    global worker

    try:
        if request.method == "GET":
            exists = worker.getIdExists(uuid)
            if isinstance(exists, Response):
                return exists
            return json.dumps(exists)
        else:
            return Response("Invalid request use GET to check the status of a UUID", 500)
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


@app.route('/file-id/<file_uuid>', methods=["GET"])
@secured(has_read=True)
def get_file_id(file_uuid):
    global worker

    try:
        file_id_info = worker.getFileIdInfo(file_uuid)
        if isinstance(file_id_info, Response): return file_id_info
        return Response(response=file_id_info, mimetype="application/json")
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


@app.route('/<uuid>/ancestors', methods=["GET"])
@secured(has_read=True)
def get_ancestors(uuid):
    global worker

    try:
        ancestors = worker.getAncestors(uuid)
        if isinstance(ancestors, Response): return ancestors
        return Response(response=ancestors, mimetype="application/json")
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


# Get the information for all files attached to a specific entity
# Example call GET to https://uuid.api.hubmapcosortium.org/<entity-id>/files
#                 with an Authorization Bearer header containing a valid HuBMAP Globus token
#
# input: id (hubmap_id or uuid) of the parent entity in path,<entity-id> above 
# output: an array of dicts with each dict containing the attributes of a file
#         file attributes:
#             path: the local file system path, including name of the file
#         checksum: the checksum of the file
#             size: the size of the file
#        file_uuid: the uuid of the file
#         base_dir: the base directory type, one of
#                      INGEST_PORTAL_UPLOAD - the file was uploaded into the space for file uploads from the Ingest UI
#                               DATA_UPLOAD - the file was upload into the upload space for datasets usually via Globus
#
#         Will return an empty array if no files are attached to the entity
#
# Returns:
#    200:  As described above on success, example below
#    400:  If id is not found
#    401:  Authentication failed
#    403:  No authorization to use this method
#    500:  An unexpected error occurred
#
# Example Output, status 200
#
#        [
#            {
#                "path": "hg19.exonic+intronic/alignment/Puck_200903_02_mapping_rate.txt",
#                "md5_checksum": "c39c7653bd0802eb875af8eb8cb9f680",
#                "size": 276,
#                "base_dir": "DATA_UPLOAD",
#                "file_uuid": "11d6412f1864ee7945f75e1f6b661dfa"
#            },
#            {
#                "path": "hg19.exonic+intronic/fastq/Puck_200903_02.read2.fastq.gz",
#                "md5_checksum": "ba8f5f30df2150834b2e1a86c2773f6a",
#                "size": 5023066884,
#                "base_dir": "DATA_UPLOAD",
#                "file_uuid": "15fad895db1472c6b9167e0f6e01762a"
#            },
#            {
#                "path": "hg19.exonic+intronic/barcode_matching/BeadBarcodes.txt",
#                "md5_checksum": "38de80f88dc451d95179db50ce5e21e5",
#                "size": 2287908,
#                "base_dir": "DATA_UPLOAD",
#                "file_uuid": "250066e0b3bd019e646d6e83a842f4d0"
#            },
#            {
#                "path": "hg19.exonic+intronic/barcode_matching/Puck_200903_02_unique_matched_illumina_barcodes.txt",
#                "md5_checksum": "12e143d90c07871c7993ce39602e93b4",
#                "size": 710310,
#                "base_dir": "DATA_UPLOAD",
#                "file_uuid": "5dd8f0a806a5d6eff9f5a64fa011691d"
#            }
#        ]

@app.route('/<entity_id>/files', methods=["GET"])
@secured(has_read=True)
def get_file_info(entity_id):
    global worker

    try:
        file_info = worker.get_file_info(entity_id)
        if isinstance(file_info, Response): return file_info
        return Response(response=json.dumps(file_info), mimetype="application/json")
    except Exception as e:
        eMsg = str(e)
        logger.error(e, exc_info=True)
        return (Response("Unexpected error: " + eMsg, 500))


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port="5001")
    except Exception as e:
        print("Error during starting debug server.")
        print(str(e))
        logger.error(e, exc_info=True)
        print("Check the log file for further information: " + LOG_FILE_NAME)
