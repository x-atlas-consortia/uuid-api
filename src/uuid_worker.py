import os
import logging

import mysql.connector.errors
from flask import Flask, Response
import threading
import secrets
import time
from contextlib import closing
import json
from app_db import DBConn
import copy

# HuBMAP commons
# from hm_auth import AuthHelper
from hubmap_commons.string_helper import isBlank, listToCommaSeparated, padLeadingZeros
from hubmap_commons.hm_auth import AuthHelper
from hubmap_commons import globus_groups

MAX_GEN_IDS = 200

APPID_ALPHA_CHARS = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z']
APPID_NUM_CHARS = ['2', '3', '4', '5', '6', '7', '8', '9']
HEX_CHARS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

from enum import Enum
class DataIdType(Enum):
    INVALID = 'invalid'
    UUID = 'UUID'
    BASE_ID = 'BASE_ID'
    SUBMISSION_ID = 'SUBMISSION_ID'

class EntityTypeUUIDPrefix(Enum):
    FILE = 'FFFF' # N.B. match the case used in the enumeration value with UUIDWorker.HEX_CHARS

# Set up scalars with SQL strings matching the paramstyle of the database module, as
# specified at https://peps.python.org/pep-0249
#
# Using the "format" paramstyle with mysql-connector-python module for MySQL 8.0+
#
# Ignore threat of unsanitized user input for SQL injection, XSS, etc. due to current
# nature of site at AWS, UUID format checking in this microservice, etc.
SQL_INSERT_UUIDS = \
    ("INSERT INTO uuids"
     " (uuid, ENTITY_TYPE, TIME_GENERATED, USER_ID, USER_EMAIL)"
     " VALUES"
     " (%s, %s, %s, %s, %s)"
     )

SQL_INSERT_UUIDS_ATTRIBUTES_DEFAULT_DESC_COUNT = \
    ("INSERT INTO uuids_attributes "
     " (UUID, BASE_ID, SUBMISSION_ID)"
     " VALUES"
     " (%s, %s, %s)"
     )

SQL_INSERT_ANCESTORS = \
    ("INSERT INTO ancestors"
     " (DESCENDANT_UUID, ANCESTOR_UUID)"
     " VALUES"
     " (%s, %s)"
     )

SQL_INSERT_FILES = \
    ("INSERT INTO files"
     " (UUID, PATH, CHECKSUM, SIZE, BASE_DIR)"
     " VALUES"
     " (%s, %s, %s, %s, %s)"
     )

SQL_SELECT_ANCESTORS_OF_DESCENDANT_UUID = \
    ("SELECT ANCESTOR_UUID"
     " FROM ancestors"
     " WHERE DESCENDANT_UUID = %s"
     )

SQL_SELECT_FILES_DESCENDED_FROM_ANCESTOR_UUID = \
    ("SELECT UUID AS uuid"
     "       ,PATH AS path"
     "       ,CHECKSUM AS checksum"
     "       ,SIZE AS size"
     "       ,BASE_DIR AS base_dir"
     "       ,ANCESTOR_UUID AS ancestor_uuid"
     " FROM files"
     "  INNER JOIN ancestors ON ancestors.DESCENDANT_UUID = files.UUID"
     " WHERE ancestors.ANCESTOR_UUID = %s"
     )

SQL_SELECT_FILES_INFO_INCLUDING_ANCESTOR = \
    ("SELECT UUID AS uuid"
     "       ,PATH AS path"
     "       ,CHECKSUM AS checksum"
     "       ,SIZE AS size"
     "       ,BASE_DIR AS base_dir"
     "       ,ANCESTOR_UUID AS ancestor_uuid"
     " FROM files"
     "  INNER JOIN ancestors ON ancestors.DESCENDANT_UUID = files.UUID"
     " WHERE files.UUID = %s"
     )

SQL_SELECT_ID_INFO_BY_UUID = \
    ("SELECT uuids.UUID AS uuid"
     "       ,uuids_attributes.BASE_ID AS base_id"
     "       ,uuids.ENTITY_TYPE AS type"
     "       ,uuids.TIME_GENERATED AS time_generated"
     "       ,uuids.USER_ID AS user_id"
     "       ,uuids_attributes.SUBMISSION_ID AS submission_id"
     "       ,uuids.USER_EMAIL AS email"
     "       ,GROUP_CONCAT(ancestors.ancestor_uuid) AS ancestor_ids"
     " FROM uuids"
     "  LEFT OUTER JOIN ancestors ON uuids.UUID = ancestors.DESCENDANT_UUID"
     "  LEFT OUTER JOIN uuids_attributes ON uuids.UUID = uuids_attributes.UUID"
     " WHERE uuids.UUID = %s"
     )

SQL_SELECT_ID_INFO_BY_BASE_ID = \
    SQL_SELECT_ID_INFO_BY_UUID.replace(" WHERE uuids.UUID = %s"
                                       , " WHERE uuids_attributes.BASE_ID = %s")
SQL_SELECT_ID_INFO_BY_SUBMISSION_ID = \
    SQL_SELECT_ID_INFO_BY_UUID.replace(" WHERE uuids.UUID = %s"
                                       , " WHERE lower(uuids_attributes.SUBMISSION_ID) = %s")

SQL_SELECT_ID_ROW_COUNT_BY_UUID = \
    ("SELECT COUNT(*) AS row_count"
     " FROM uuids"
     " WHERE uuids.UUID = %s"
     )

SQL_SELECT_ID_ROW_COUNT_BY_BASE_ID = \
    ("SELECT COUNT(*) AS row_count"
     " FROM uuids_attributes"
     " WHERE uuids_attributes.BASE_ID = %s"
     )

SQL_SELECT_ID_ROW_COUNT_BY_SUBMISSION_ID = \
    SQL_SELECT_ID_ROW_COUNT_BY_BASE_ID.replace(" WHERE uuids_attributes.BASE_ID = %s"
                                               , " WHERE uuids_attributes.SUBMISSION_ID = %s")

SQL_SELECT_UUIDS_IN_LIST = \
    ("SELECT UUID"
     " FROM uuids"
     " WHERE uuids.UUID IN (%s)"
     )

SQL_SELECT_BASE_IDS_IN_LIST = \
    ("SELECT BASE_ID"
     " FROM uuids_attributes"
     " WHERE uuids_attributes.BASE_ID IN (%s)"
     )

SQL_SELECT_ANCESTOR_FOR_DESCENDANT_COUNT_UPDATE = \
    ("SELECT uuids.ENTITY_TYPE AS entity_type"
     "       ,uuids_attributes.DESCENDANT_COUNT as descendant_count"
     "       ,uuids_attributes.SUBMISSION_ID as submission_id"
     " FROM uuids"
     "  INNER JOIN uuids_attributes ON uuids.UUID = uuids_attributes.UUID"
     " WHERE uuids.UUID = %s"
     )

SQL_UPDATE_ANCESTOR_DESCENDANT_COUNT = \
    ("UPDATE uuids_attributes"
     " SET DESCENDANT_COUNT = %s"
     " WHERE UUID = %s"
     )

SQL_SELECT_ORGAN_COUNT_BY_DONOR_AND_CODE = \
    ("SELECT ORGAN_COUNT"
     " FROM organs"
     " WHERE DONOR_UUID = %s AND organ_code = %s"
     )

SQL_INSERT_ORGANS = \
    ("INSERT INTO organs"
     " (DONOR_UUID, ORGAN_CODE, ORGAN_COUNT)"
     " VALUES"
     " (%s, %s, %s)"
     )

SQL_UPDATE_ORGAN_COUNT = \
    ("UPDATE organs"
     " SET ORGAN_COUNT = %s"
     " WHERE DONOR_UUID = %s AND ORGAN_CODE = %s"
     )

SQL_SELECT_PARENT_DATA_CENTERS = \
    ("SELECT UUID"
     "       ,DC_CODE"
     " FROM data_centers"
     " WHERE uuid = %s OR dc_uuid = %s"
     )

SQL_INSERT_LAB_WITH_TMC_PREFIX = \
    ("INSERT INTO data_centers"
     " (UUID, DC_UUID, DC_CODE)"
     " VALUES"
     " (%s, %s, %s)"
     )

def startsWithComponentPrefix(app_id):
    tidl = app_id.strip().lower()
    if tidl.startswith('test') or tidl.startswith('van') or tidl.startswith('ufl') or tidl.startswith(
            'stan') or tidl.startswith('ucsd') or tidl.startswith('calt') or tidl.startswith(
        'rtibd') or tidl.startswith('rtige') or tidl.startswith('rtinw') or tidl.startswith(
        'rtist') or tidl.startswith('ttdct') or tidl.startswith('ttdhv') or tidl.startswith(
        'ttdpd') or tidl.startswith('ttdst') or tidl.startswith('chop') or tidl.startswith(
        'hca') or tidl.startswith('pnnlnu') or tidl.startswith('psucu') or tidl.startswith(
        'tmcpnnl') or tidl.startswith('ttdpnnl') or tidl.startswith('uconn') or tidl.startswith(
        'ucsdcoh') or tidl.startswith('ucsdfr') or tidl.startswith('upenn') or tidl.startswith('yale'):
        return True
    else:
        return False

# Return a recognized value in DataIdType for the data designed to
# be in a known database column
def getDataColumnIdType(dbColumn):
    column_name = dbColumn.strip().upper()
    if column_name == 'SUBMISSION_ID':
        return DataIdType.SUBMISSION_ID
    elif column_name == 'BASE_ID':
        return DataIdType.BASE_ID
    elif column_name == 'UUID':
        return DataIdType.UUID
    return DataIdType.INVALID

# Return the type of the identifier from the recognized values in DataIdType
def getDataIdType(identifier):
    if not isValidAppId(identifier):
        return DataIdType.INVALID
    if startsWithComponentPrefix(identifier):
        return DataIdType.SUBMISSION_ID
    tid = stripAppId(identifier)
    if len(tid) == 10:
        return DataIdType.BASE_ID
    if len(tid) == 32:
        return DataIdType.UUID
    # Never get here, if isValidAppId() called at beginning
    return DataIdType.INVALID


def isValidAppId(app_id):
    if isBlank(app_id): return False
    if startsWithComponentPrefix(app_id):
        return True
    tid = stripAppId(app_id)
    l = len(tid)
    if not (l == 10 or l == 32): return False
    tid = tid.upper()
    if l == 10:
        if not set(tid[0:3]).issubset(APPID_NUM_CHARS): return False
        if not set(tid[3:7]).issubset(APPID_ALPHA_CHARS): return False
        if not set(tid[7:]).issubset(APPID_NUM_CHARS): return False
    if l == 32:
        if not set(tid).issubset(HEX_CHARS): return False
    return True


def stripAppId(app_id):
    if isBlank(app_id): return app_id
    thmid = app_id.strip();
    if thmid.lower().startswith(APP_ID_PREFIX.lower()):
        thmid = thmid[3:]
    if thmid.startswith(':'): thmid = thmid[1:]
    return thmid.strip().replace('-', '').replace('.', '').replace(' ', '')


class UUIDWorker:
    authHelper = None

    def __init__(self, globusGroups=None, app_config=None):
        global APP_ID_PREFIX
        global APP_ID
        global APP_UUID
        global APP_BASE_ID
        global BASE_DIR_TYPES
        global ID_ENTITY_TYPES
        global ANCESTOR_REQUIRED_ENTITY_TYPES
        global MULTIPLE_ALLOWED_ORGANS
        global SUBMISSION_ID_ENTITY_TYPES

        self.logger = logging.getLogger('uuid.service')

        if app_config is None:
            raise Exception("Configuration data loaded by the app must be passed to the worker.")
        try:
            clientId = app_config['APP_CLIENT_ID']
            clientSecret = app_config['APP_CLIENT_SECRET']
            dbHost = app_config['DB_HOST']
            dbName = app_config['DB_NAME']
            dbUsername = app_config['DB_USERNAME']
            dbPassword = app_config['DB_PASSWORD']

            # These application specific IDs are used to generalize the uuid-api to allow it to work with specific instances of entity-api
            APP_ID_PREFIX = app_config['APP_ID_PREFIX']
            APP_ID = app_config['APP_ID']
            APP_UUID = app_config['APP_UUID']
            APP_BASE_ID = app_config['APP_BASE_ID']

            BASE_DIR_TYPES = app_config['BASE_DIR_TYPES']
            ID_ENTITY_TYPES = app_config['ID_ENTITY_TYPES']
            ANCESTOR_REQUIRED_ENTITY_TYPES = app_config['ANCESTOR_REQUIRED_ENTITY_TYPES']
            MULTIPLE_ALLOWED_ORGANS = app_config['MULTIPLE_ALLOWED_ORGANS']
            SUBMISSION_ID_ENTITY_TYPES = app_config['SUBMISSION_ID_ENTITY_TYPES']

            if not clientId:
                raise Exception("Configuration parameter APP_CLIENT_ID not valid.")
            if not clientSecret:
                raise Exception("Configuration parameter APP_CLIENT_SECRET not valid.")
        except KeyError as ke:
            self.logger.error("Expected configuration failed to load %s from app_config=%s.",ke,app_config)
            raise Exception("Expected configuration failed to load. See the logs.")

        if not clientId  or not clientSecret:
            raise Exception("Globus client id and secret are required in AuthHelper")

        if not AuthHelper.isInitialized():
            # Depending on the version of the AuthHelper, the globusGroups variable might not be support
            try:
                self.authHelper = AuthHelper.create(clientId=clientId, clientSecret=clientSecret,
                                                    globusGroups=globusGroups)
            except TypeError:
                self.authHelper = AuthHelper.create(clientId=clientId, clientSecret=clientSecret)
        else:
            self.authHelper.instance()

        self.dbHost = dbHost
        self.dbName = dbName
        self.dbUsername = dbUsername
        self.dbPassword = dbPassword
        self.lock = threading.RLock()
        self.hmdb = DBConn(self.dbHost, self.dbUsername, self.dbPassword, self.dbName)

        # Deprecate the use of Provenance
        # self.prov_helper = Provenance(clientId, clientSecret, None)

    def __resolve_lab_id(self, lab_id, user_id, user_email):
        if isBlank(lab_id):
            return None
        check_id = lab_id.strip().lower()
        r_val = {}
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_PARENT_DATA_CENTERS
                             ,(check_id, check_id))
                result = curs.fetchone()
                if result is None:
                    try:
                        # Deprecate the use of Provenance
                        # lab = self.prov_helper.get_group_by_identifier(check_id)

                        # Get the globus groups info based on the groups json file in commons package
                        globus_groups_info = globus_groups.get_globus_groups_info()
                        groups_by_tmc_prefix_dict = globus_groups_info['by_tmc_prefix']
                        if not check_id in groups_by_tmc_prefix_dict:
                            lab = {}
                        else:
                            lab = groups_by_tmc_prefix_dict[check_id]
                    except ValueError:
                        return Response("A valid lab with specified id not found id:" + check_id, 400)

                    if not 'tmc_prefix' in lab:
                        return Response("Lab with specified id:" + check_id + " does not contain a tmc_prefix.", 400)
                    # As of May 2022, know issue that code in the rest of this block is not reached.
                    # The code above will return a message like:
                    # "Lab with specified id:ttdst does not contain a tmc_prefix."
                    # when TTDST is passed in from the client due to lower() being called on
                    # the input, the Globus config JSON containing the name in uppercase, and
                    # Python dictionaries being case sensitive.

                    uuid_json = self.newUUIDs([], "LAB", user_id, user_email, 1, gen_base_ids=False)
                    uuid_info = json.loads(uuid_json)
                    r_val['dc_code'] = lab['tmc_prefix']
                    r_val['uuid'] = uuid_info[0]['uuid']
                    curs.execute(SQL_INSERT_LAB_WITH_TMC_PREFIX
                                 , (check_id, check_id))
                    dbConn.commit()
                else:
                    r_val['dc_code'] = result[1]
                    r_val['uuid'] = result[0]
        return r_val

    def uuidPost(self, req, nIds):
        userInfo = self.authHelper.getUserInfoUsingRequest(req)
        if isinstance(userInfo, Response):
            return userInfo;

        if not 'sub' in userInfo:
            return Response("Unable to get user id (sub) via introspection", 400)

        userId = userInfo['sub']
        userEmail = None
        if 'email' in userInfo:
            userEmail = userInfo['email']

        if not req.is_json:
            return (Response("Invalid input, json required.", 400))
        content = req.get_json()
        if content is None or len(content) <= 0:
            return (Response("Invalid input, uuid attributes required", 400))
        if not 'entity_type' in content or isBlank(content['entity_type']):
            return (Response("entity_type is a required attribute", 400))

        entityType = content['entity_type'].upper().strip()
        organ_code = None
        if 'organ_code' in content and not isBlank(content['organ_code']):
            if not entityType == 'SAMPLE':
                return (Response("Organ code " + content[
                    'organ_code'] + " found for entity type of " + entityType + ", but SAMPLE entity type required to specify organ.",
                                 400))
            organ_code = content['organ_code'].strip().upper()

        parentIds = None
        if ('parent_ids' in content):
            parentIds = content['parent_ids']

        if (entityType in ANCESTOR_REQUIRED_ENTITY_TYPES and parentIds is None):
            return (
                Response("parentId is a required attribute for entities " + ", ".join(ANCESTOR_REQUIRED_ENTITY_TYPES),
                         400))

        lab_code = None

        if not parentIds is None:
            if (entityType in SUBMISSION_ID_ENTITY_TYPES):
                n_parents = len(parentIds)
                if n_parents != 1:
                    return (Response("Entity type " + entityType + " requires a single ancestor id, " + str(
                        n_parents) + " provided.", 400))

        if entityType == "DONOR" or entityType == "SOURCE" or entityType == 'UPLOAD':
            ancestor_ids = []
            lab_info = self.__resolve_lab_id(parentIds[0], userId, userEmail)
            if isinstance(lab_info, Response):
                return lab_info
            ancestor_ids.append(lab_info['uuid'])
            lab_code = lab_info['dc_code']
        elif parentIds is None:
            ancestor_ids = []
        else:
            ancestor_ids = parentIds

        file_info = None
        base_dir = None
        if entityType == "FILE":
            if not 'file_info' in content:
                return (Response("Entity type of FILE requires a file_info array provide in the request body.", 400))
            file_info = content['file_info']
            if not isinstance(file_info, list):
                return (Response("file_info attribute must be a list", 400))
            if not len(file_info) == nIds:
                return (Response(
                    "number file_info list must contain the same number of entries as ids being generated " + str(nIds),
                    400))
            for fi in file_info:
                if not 'path' in fi or isBlank(fi['path']):
                    return (Response("The 'path' attribute is required for each file_info entry", 400))
                if not 'base_dir' in fi or isBlank(fi['base_dir']):
                    return (Response(
                        "the 'base_dir' attribute is required for each file_info entity.  Valid values are " + " ".join(
                            BASE_DIR_TYPES), 400))
                base_dir = fi['base_dir'].strip().upper()
                if not base_dir in BASE_DIR_TYPES:
                    return (Response("valid base_dir values are " + " ".join(BASE_DIR_TYPES), 400))
        for parentId in ancestor_ids:
            if not self.uuid_exists(parentId):
                return (Response("Parent id " + parentId + " does not exist", 400))

        return self.newUUIDs(ancestor_ids, entityType, userId, userEmail, nIds, organ_code=organ_code,
                             lab_code=lab_code, file_info_array=file_info, base_dir_type=base_dir)

    '''
    def uuidPut(self, req):
        if not req.is_json:
            return(Response("Invalid input, json required.", 400))
        content = req.get_json()
        if content is None or len(content) <= 0:
            return(Response("Invalid input, hubmap-uuids and display-ids arrays required", 400))
        if (not 'hubmap-uuids' in content) or content['hubmap-uuids'] is None or (not isinstance(content['hubmap-uuids'], list)) or (not len(content['hubmap-uuids']) > 0):
            return(Response("hubmap-uuids is a required attribute", 400))
        if (not 'display-ids' in content) or content['display-ids'] is None or (not isinstance(content['display-ids'], list) or (not len(content['display-ids']) > 0)):
            return(Response("display-ids is a required attribute", 400))

        uuids = content['hubmap-uuids']
        disp_ids = content['display-ids']

        if len(uuids) != len(disp_ids):
            return(Response("The length of the diplay-ids and hubmap-uuids arrays must be the same length", 400))

        return self.updateUUIDs(uuids, disp_ids)
    '''

    def newUUIDTest(self, parentIds, entityType, userId, userEmail):
        return self.newUUIDs(parentIds, entityType, userId, userEmail)

    # Generate random UUIDs, but with a fixed prefix when configured for
    # the entity_type.
    def v2UUIDGen(self,uuid_entity_type):
        hexVal = ""
        if uuid_entity_type == 'FILE':
            hexVal = EntityTypeUUIDPrefix.FILE.value

        while len(hexVal) < 32:
            hexVal = hexVal + secrets.choice(HEX_CHARS)

        # If we ended up with a UUID starting with the prefix for a FILE while trying to
        # get a UUID for a non-FILE, loop until the prefix is acceptable.
        while uuid_entity_type != 'FILE' and hexVal[:len(EntityTypeUUIDPrefix.FILE.value)] == EntityTypeUUIDPrefix.FILE.value:
            prefixLength = len(EntityTypeUUIDPrefix.FILE.value)
            substitutePrefix = ""
            while len(substitutePrefix) < prefixLength:
                substitutePrefix = substitutePrefix + secrets.choice(HEX_CHARS)
            hexVal = substitutePrefix + hexVal[prefixLength:]

        hexVal = hexVal.lower()
        return hexVal

    # Not used for SenNet
    def __create_submission_ids(self, num_to_gen, parent_id, entity_type, organ_code=None, lab_code=None):
        parent_id = parent_id.strip().lower()
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_ANCESTOR_FOR_DESCENDANT_COUNT_UPDATE
                             ,( parent_id, ) )  # N.B. comma to force creation of tuple with one value, rather than scalar
                results = curs.fetchone()
                anc_entity_type = results[0]
                desc_count = results[1]
                anc_submission_id = results[2]
                # a donor
                if entity_type == 'DONOR':
                    if not anc_entity_type == 'LAB':
                        return Response(
                            "An id can't be created for a DONOR because a DATA CENTER is required as the direct ancestor and an ancestor of type " + anc_entity_type + " found.",
                            400)
                    if isBlank(lab_code):
                        return Response(
                            "No data center code found data center with uuid:" + parent_id + ". Unable to generate an id for a DONOR.",
                            400)
                    r_val = []
                    for _ in range(0, num_to_gen):
                        desc_count = desc_count + 1
                        r_val.append(lab_code.strip().upper() + padLeadingZeros(desc_count, 4))
                    curs.execute(SQL_UPDATE_ANCESTOR_DESCENDANT_COUNT
                                 , (str(desc_count), parent_id))
                    dbConn.commit()
                    return r_val
                # a SOURCE is only used in SenNet, and SenNet does not use SUBMISSION_ID
                # an organ
                elif entity_type == 'SAMPLE' and (anc_entity_type == 'DONOR' or anc_entity_type == 'SOURCE'):
                    if isBlank(organ_code):
                        return Response(
                            "An id can't be created for a SAMPLE because the immediate ancestor is a DONOR and the SAMPLE was not supplied with an associated organ code (SAMPLE must be an organ to have a DONOR as a direct ancestor)",
                            400)
                    organ_code = organ_code.strip().upper()
                    curs.execute(SQL_SELECT_ORGAN_COUNT_BY_DONOR_AND_CODE
                                 , (parent_id, organ_code))
                    org_res = curs.fetchone()
                    if org_res is None:
                        curs.execute(SQL_INSERT_ORGANS
                                     , (parent_id, organ_code, 0))
                        dbConn.commit()
                        org_count = 0
                    else:
                        org_count = org_res[0]
                    if not organ_code in MULTIPLE_ALLOWED_ORGANS:
                        if org_count >= 1:
                            return Response(
                                "Cannot add another organ of type " + organ_code + " to DONOR " + parent_id + " exists already.",
                                400)
                        if num_to_gen > 1:
                            return Response(
                                "Cannot create multiple submission ids for organ of type " + organ_code + ". " + str(
                                    num_to_gen) + " requested.", 400)
                        org_count = 1
                        r_val = [anc_submission_id + "-" + organ_code]
                    else:
                        r_val = []
                        for _ in range(0, num_to_gen):
                            org_count = org_count + 1
                            r_val.append(anc_submission_id + "-" + organ_code + padLeadingZeros(org_count, 2))
                    curs.execute(SQL_UPDATE_ORGAN_COUNT
                                 , (str(org_count), parent_id, organ_code))
                    dbConn.commit()
                    return r_val

                # error if remaining non-organ samples are not the descendants of a SAMPLE
                elif entity_type == 'SAMPLE' and not anc_entity_type == 'SAMPLE':
                    return Response(
                        "Cannot create a submission id for a SAMPLE with a direct ancestor of " + anc_entity_type, 400)
                elif entity_type == 'SAMPLE':
                    r_val = []
                    for _ in range(0, num_to_gen):
                        desc_count = desc_count + 1
                        r_val.append(anc_submission_id + "-" + str(desc_count))
                    curs.execute(SQL_UPDATE_ANCESTOR_DESCENDANT_COUNT
                                 , (str(desc_count), parent_id))
                    dbConn.commit()
                    return r_val
                else:
                    return Response("Cannot create a submission id for an entity of type " + entity_type, 400)

    # generate multiple ids, one for each display id in the displayIds array

    def newUUIDs(self, parentIDs, entityType, userId, userEmail, nIds, organ_code=None, lab_code=None,
                 file_info_array=None, base_dir_type=None):
        # if entityType == 'DONOR':
        gen_base_ids = entityType in ID_ENTITY_TYPES
        returnIds = []
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        store_file_info = False
        if entityType == 'FILE':
            store_file_info = True
        with self.lock:
            # generate in batches
            previousUUIDs = set()
            previous_app_ids = set()

            gen_submission_ids = False
            if entityType in SUBMISSION_ID_ENTITY_TYPES:
                gen_submission_ids = True

            # set a flag indicating if a UUID attributes row will be created for
            # the UUID row that will be created.
            # N.B. descendant_count is tied to gen_submission_ids i.e. will not need a
            #      row to support descendant_count unless submission_id is populated.
            insert_attributes_for_uuid = gen_base_ids or gen_submission_ids

            for i in range(0, nIds, MAX_GEN_IDS):
                insertVals = []
                insertAttribVals = []
                file_info_insert_vals = []
                insertParents = []
                numToGen = min(MAX_GEN_IDS, nIds - i)
                # generate uuids
                uuids = self.__nUniqueIds(numToGen, lambda: self.v2UUIDGen(entityType), 'uuid', previousGeneratedIds=previousUUIDs)
                if gen_base_ids:
                    app_base_ids = self.__nUniqueIds(numToGen, self.hmidGen, 'base_id',
                                                     previousGeneratedIds=previous_app_ids)
                else:
                    app_base_ids = [None] * numToGen

                submission_ids = None
                if gen_submission_ids:
                    submission_ids = self.__create_submission_ids(numToGen, parentIDs[0], entityType,
                                                                  organ_code=organ_code, lab_code=lab_code)
                    if isinstance(submission_ids, Response):
                        return submission_ids

                for n in range(0, numToGen):
                    insUuid = uuids[n]
                    previousUUIDs.add(insUuid)
                    thisId = {"uuid": insUuid}

                    if gen_base_ids:
                        ins_app_base_id = app_base_ids[n]
                        previous_app_ids.add(ins_app_base_id)
                        ins_display_app_id = self.__display_app_id(ins_app_base_id)
                        thisId[APP_BASE_ID] = ins_app_base_id
                        thisId[APP_ID] = ins_display_app_id
                    else:
                        ins_app_base_id = None

                    if gen_submission_ids:
                        thisId["submission_id"] = submission_ids[n]
                    #     insRow = (insUuid, ins_app_base_id, entityType, now, userId, userEmail, submission_ids[n])
                    # else:
                    #     insRow = (insUuid, ins_app_base_id, entityType, now, userId, userEmail)

                    # Only set the attributes tuple of committing attributes to the table besides the UUID
                    insertVals.append((insUuid, entityType, now, userId, userEmail))
                    if insert_attributes_for_uuid:
                        insertAttribVals.append((insUuid, ins_app_base_id, submission_ids[n] if gen_submission_ids else None))

                    if store_file_info:
                        info_idx = i + n
                        file_path = file_info_array[info_idx]['path']
                        # replace any <uuid> tags in the file path with the generated uuid
                        file_path = file_path.replace('<uuid>', insUuid)
                        file_checksum = None
                        file_size = None
                        if 'checksum' in file_info_array[info_idx]:
                            file_checksum = file_info_array[info_idx]['checksum']
                        if 'size' in file_info_array[info_idx]:
                            file_size = file_info_array[info_idx]['size']
                        file_info_ins_row = (insUuid, file_path, file_checksum, file_size, base_dir_type)
                        # file_info_ins_row = (insUuid, file_path, file_checksum)
                        file_info_insert_vals.append(file_info_ins_row)
                        thisId['file_path'] = file_path

                    returnIds.append(thisId)

                    for parentId in parentIDs:
                        parRow = (insUuid, parentId)
                        insertParents.append(parRow)

                with closing(self.hmdb.getDBConnection()) as dbConn:

                    existing_autocommit_setting = dbConn.autocommit
                    dbConn.autocommit = False

                    try:
                        with closing(dbConn.cursor(prepared=True)) as curs:
                            # Count on DBAPI-compliant MySQL Connector/Python to begin a transaction on the first
                            # SQL statement and keep open until explicit commit() call to allow rollback(), so
                            # uuid and uuid_attributes committed atomically.
                            curs.executemany(SQL_INSERT_UUIDS
                                             ,insertVals)
                            if insertAttribVals:
                                curs.executemany(SQL_INSERT_UUIDS_ATTRIBUTES_DEFAULT_DESC_COUNT
                                                 ,insertAttribVals)

                            if store_file_info:
                                curs.executemany(SQL_INSERT_FILES, file_info_insert_vals)

                            curs.executemany(SQL_INSERT_ANCESTORS, insertParents)
                        dbConn.commit()
                    except mysql.connector.errors.Error as dbErr:
                        dbConn.rollback()
                        self.logger.error("newUUIDs() database INSERT failure caused rollback: ", dbErr, ", nIds=", nIds, ", userId=", userId)

                        raise dbErr
                    finally:
                        # restore the autocommit setting, even though closing it by going out of scope.
                        dbConn.autocommit = existing_autocommit_setting

        return json.dumps(returnIds)

    # generate unique ids
    # generates ids with provided id generation method and checks them against existing ids in the DB
    # this method MUST BE CALLED FROM WITHIN a self.lock block
    def __nUniqueIds(self, nIds, idGenMethod, dbColumn, previousGeneratedIds=set(), iteration=1):
        ids = set()
        lclPreviousIds = copy.deepcopy(previousGeneratedIds)
        for _ in range(nIds):
            newId = idGenMethod()
            count = 1
            while (newId in ids or newId in lclPreviousIds) and count < 100:
                newId = idGenMethod()
                count = count + 1
            if count == 100:
                raise Exception("Unable to generate an initial unique id for " + dbColumn + " after 100 attempts.")
            ids.add(newId)
            lclPreviousIds.add(newId)
        dupes = self.__findDupsInDB(dbColumn, ids)
        if dupes is not None and len(dupes) > 0:
            n_iter = iteration + 1
            if n_iter > 100:
                raise Exception("Unable to generate unique id(s) for " + dbColumn + " after 100 attempts.")
            replacements = self.__nUniqueIds(len(dupes), idGenMethod, dbColumn, previousGeneratedIds=lclPreviousIds,
                                             iteration=n_iter)
            for val in dupes:
                ids.remove(val[0])
            for val in replacements:
                ids.add(val)
        return list(ids)

    def __findDupsInDB(self, dbColumn, idSet):

        # Determine the type of identifier expected in the column so
        # the correct prepared statement can be used.
        data_id_type = getDataColumnIdType(dbColumn)

        # form a tuple containing one string with the identifiers passed in, with
        # each element quoted as required by MySQL, to be used
        # by parameter substitution in the prepared statement.
        id_list = (listToCommaSeparated(    idSet,
                                            "'",
                                            True),) # N.B. comma to force creation of tuple with one value, rather than scalar

        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                if data_id_type == DataIdType.BASE_ID:
                    curs.execute(SQL_SELECT_BASE_IDS_IN_LIST
                                 , id_list)
                elif data_id_type == DataIdType.UUID:
                    curs.execute(SQL_SELECT_UUIDS_IN_LIST
                                 , id_list)
                else:
                    self.logger.error("Unable to retrieve identfiers when data_id_type=",data_id_type," dbColumn=",dbColumn,".")
                    pass
                dupes = curs.fetchall()
        return dupes

    ''' 
    Unused since updateUUIDs() disabled in Jan 2021
    # which items in idSet are not in the database
    def __findExclusionsInDB(self, dbColumn, idSet):

        sql = "select " + dbColumn + " from ( "
        first = True
        for ex_id in idSet:
            if first:
                first = False
            else:
                sql = sql + " UNION ALL "
            sql = sql + "(select '" + ex_id + "' as " + dbColumn + ")"
        sql = sql + ") as list left join uuids using (" + dbColumn + ") where uuids." + dbColumn + " is null"
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute(sql)
                excluded = curs.fetchall()

        return excluded
    '''

    def __display_app_id(self, base_id):
        new_id = APP_ID_PREFIX + base_id[0:3] + '.' + base_id[3:7] + '.' + base_id[7:]
        return new_id

    def hmidGen(self):
        nums1 = ''
        nums2 = ''
        alphs = ''
        for _ in range(3):
            nums1 = nums1 + secrets.choice(APPID_NUM_CHARS)  # [random.randint(0,len(DOI_NUM_CHARS)-1)]
        for _ in range(3):
            nums2 = nums2 + secrets.choice(APPID_NUM_CHARS)  # [random.randint(0,len(DOI_NUM_CHARS)-1)]
        for _ in range(4):
            alphs = alphs + secrets.choice(APPID_ALPHA_CHARS)  # [random.randint(0,len(DOI_ALPHA_CHARS)-1)]

        val = nums1 + alphs + nums2
        return (val)

    def getIdExists(self, hmid):
        if not isValidAppId(hmid):
            return Response("Invalid Id", 400)
        tid = stripAppId(hmid)
        if startsWithComponentPrefix(hmid):
            return self.submission_id_exists(hmid.strip())
        elif len(tid) == 10:
            return self.base_id_exists(tid.upper())
        elif len(tid) == 32:
            return self.uuid_exists(tid.lower())
        else:
            return Response("Invalid Id (or empty or bad length)", 400)

    # convert csv list of ancestor ids to a list
    # convert hubmap base id to a hubmap id (display version)
    def _convert_result_id_array(self, results, hmid):
        if isinstance(results, list):
            asize = len(results)
            if asize == 0:
                record = None
            elif asize == 1:
                record = results[0]
                if not 'ancestor_ids' in record:
                    return record
                ancestor_ids = record['ancestor_ids']
                if ancestor_ids is None or ancestor_ids.strip() == '':
                    record.pop('ancestor_ids', '')
                elif isinstance(ancestor_ids, str):
                    record['ancestor_ids'] = ancestor_ids.split(',')
                    if len(record['ancestor_ids']) == 1:
                        record['ancestor_id'] = record['ancestor_ids'][0]
                else:
                    raise Exception("Unknown ancestor type for id:" + hmid)

                if 'base_id' in record and record[
                    'base_id'] is not None:
                    if not record['base_id'].strip() == '':
                        record[APP_ID] = self.__display_app_id(record['base_id'])
                    record.pop('base_id', '')
            else:
                raise Exception("Multiple results exist for id:" + hmid)

        return record

    def getIdInfo(self, app_id):
        if not isValidAppId(app_id):
            return Response(app_id + " is not a valid id format", 400)

        tidl = (app_id.strip().lower(),)  # N.B. comma to force creation of tuple with one value, rather than scalar
        tid = (stripAppId(app_id),)  # N.B. comma to force creation of tuple with one value, rather than scalar

        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                try:
                    # execute() parameter substitution queries with a data tuple, each appropriate
                    # for the type of identifier provided and return fields expected.
                    data_id_type = getDataIdType(app_id)
                    if data_id_type == DataIdType.SUBMISSION_ID:
                        curs.execute(SQL_SELECT_ID_INFO_BY_SUBMISSION_ID
                                     , tidl)
                    elif data_id_type == DataIdType.BASE_ID:
                        curs.execute(SQL_SELECT_ID_INFO_BY_BASE_ID
                                     , tid)
                    elif data_id_type == DataIdType.UUID:
                        curs.execute(SQL_SELECT_ID_INFO_BY_UUID
                                     , tid)
                    else:
                        self.logger.error("Unable to retrieve identfier information when data_id_type=", data_id_type, " app_id=", app_id, ".")
                        pass
                except BaseException as err:
                    self.logger.error("Unexpected database problem. err=",err,". Verify schema is current model.")
                    raise
                results = [dict((curs.description[i][0], value) for i, value in enumerate(row)) for row in
                           curs.fetchall()]
                # remove the submission_id column if it is null
                for item in results:
                    if 'submission_id' in item and item['submission_id'] == None:
                        item.pop('submission_id')
                    if 'ancestor_ids' in item and (item['ancestor_ids'] == None or len(item['ancestor_ids']) == 0):
                        item.pop('ancestor_ids')

        # In Python, empty sequences (strings, lists, tuples) are false
        if results is None or not results:
            return Response("Could not find the target id: " + app_id, 404)
        if isinstance(results, list) and (len(results) == 0):
            return Response("Could not find the target id: " + app_id, 404)
        if not 'uuid' in results[0]:
            return Response("Could not find the target id: " + app_id, 404)
        if results[0]['uuid'] is None:
            return Response("Could not find the target id: " + app_id, 404)

        rdict = self._convert_result_id_array(results, app_id)
        rdict = self.modify_app_specific_uuid(rdict)
        return json.dumps(rdict, indent=4, sort_keys=True, default=str)

    def getAncestors(self, app_id):
        if not isValidAppId(app_id) or getDataIdType(app_id) != DataIdType.UUID:
            return Response(app_id + " is not a valid uuid", 400)
        tid = (stripAppId(app_id).lower(),)  # N.B. comma to force creation of tuple with one value, rather than scalar

        with closing(self.hmdb.getDBConnection()) as dbConn:
            results = []
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_ANCESTORS_OF_DESCENDANT_UUID
                             , tid)
                for aid in curs.fetchall():
                    results.append(aid[0])

        # In Python, empty sequences (strings, lists, tuples) are false
        if results is None or not results:
            return Response("Could not find the target id: " + app_id, 404)
        if isinstance(results, list) and (len(results) == 0):
            return Response("Could not find the target id or target id has no ancestors: " + app_id, 404)
            # kbkbkb- shouldn't we just return [], as we do elsewhere, when no ancestors?

        return json.dumps(results, indent=4, sort_keys=True, default=str)

    def getFileIdInfo(self, fid):
        if not isValidAppId(fid) or getDataIdType(fid) != DataIdType.UUID:
            # if isBlank(check_id) or len(check_id) != 32:
            return Response("Invalid file id format.  32 digit hex only.", 400)
        # sql = "select uuid, path, checksum, size, base_dir, ancestor_uuid from files inner join ancestors on ancestors.descendant_uuid = files.uuid where uuid = '" + check_id + "'"
        check_id = (fid.strip(),)  # N.B. comma to force creation of tuple with one value, rather than scalar

        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_FILES_INFO_INCLUDING_ANCESTOR
                             , check_id)
                results = [dict((curs.description[i][0], value) for i, value in enumerate(row)) for row in
                           curs.fetchall()]

        if results is None or not results:
            return Response("Could not find the target id: " + fid, 404)
        if isinstance(results, list) and (len(results) == 0):
            return Response("Could not find the target id: " + fid, 404)
        if not 'uuid' in results[0]:
            return Response("Could not find the target id: " + fid, 404)
        if results[0]['uuid'] is None:
            return Response("Could not find the target id: " + fid, 404)

        rdict = self._convert_result_id_array(results, check_id[0])
        if 'checksum' in rdict and rdict['checksum'] is None: rdict.pop('checksum')
        if 'size' in rdict and rdict['size'] is None: rdict.pop('size')

        rdict = self.modify_app_specific_uuid(rdict)
        return json.dumps(rdict, indent=4, sort_keys=True, default=str)

    def uuid_exists(self, app_id):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_ID_ROW_COUNT_BY_UUID
                             , (app_id,)) # N.B. comma to force creation of tuple with one value, rather than scalar
                res = curs.fetchone()

        if (res is None or len(res) == 0): return False
        if (res[0] == 1): return True
        if (res[0] == 0): return False
        raise Exception("Multiple uuids found matching " + app_id)

    def base_id_exists(self, base_id):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_ID_ROW_COUNT_BY_BASE_ID
                             , (base_id,)) # N.B. comma to force creation of tuple with one value, rather than scalar
                res = curs.fetchone()
        if (res is None or len(res) == 0): return False
        if (res[0] == 1): return True
        if (res[0] == 0): return False
        raise Exception("Multiple base ids found matching " + base_id)

    # Only used for HubMap
    def submission_id_exists(self, hmid):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                curs.execute(SQL_SELECT_ID_ROW_COUNT_BY_SUBMISSION_ID
                             , (hmid,)) # N.B. comma to force creation of tuple with one value, rather than scalar
                res = curs.fetchone()
        if (res is None or len(res) == 0): return False
        if (res[0] == 1): return True
        if (res[0] == 0): return False
        raise Exception("Multiple HuBMAP IDs found matching " + hmid)

    def modify_app_specific_uuid(self, dict):
        dict[APP_UUID] = dict['uuid']
        del dict['uuid']
        return dict

    def testConnection(self):
        try:
            res = None
            with closing(self.hmdb.getDBConnection()) as dbConn:
                with closing(dbConn.cursor(prepared=True)) as curs:
                    curs.execute("select 'ANYTHING'")
                    res = curs.fetchone()

            if (res is None or len(res) == 0): return False
            if (res[0] == 'ANYTHING'):
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(e, exc_info=True)
            return False

    # get the information for all files attached to a specific entity
    # input: id (hubmap_id or uuid) of the parent entity
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
    def get_file_info(self, entity_id):
        # The info is a pretty print json string
        info = self.getIdInfo(entity_id)

        # if getIdInfo returns a Response, it is sending an error back
        if isinstance(info, Response):
            return info
        # convert to dict
        info_d = json.loads(info)

        if not APP_UUID in info_d:
            return Response("Error: not corresponding UUID found for " + entity_id, 400)

        # entity_uuid = info_d[APP_UUID]
        #kbkbkb-Is this APP_UUID the same piece of data found in app.cfg i.e. 'hm_uuid' or 'sn_uuid'???
        entity_uuid = (info_d[APP_UUID],)  # N.B. comma to force creation of tuple with one value, rather than scalar

        # run the query and morph results to an array of dict
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor(prepared=True)) as curs:
                # query that finds all files associated with entity by joining the ancestors table (entity is
                # the ancestor, files are the descendants) with the files table
                curs.execute(SQL_SELECT_FILES_DESCENDED_FROM_ANCESTOR_UUID
                             , entity_uuid)
                results = [dict((curs.description[i][0].lower(), value) for i, value in enumerate(row)) for row in
                           curs.fetchall()]

        # remove unneeded result columns and change the name of base_id to file_uuid
        for item in results:
            item['file_uuid'] = item['uuid']
            item.pop('uuid')
            # item.pop('descendant_uuid')
            item.pop('ancestor_uuid')
        return results

''' 
    def newUUID(self, parentID, entityType, userId, userEmail, submissionId=None):
        uuid = self.uuidGen() #uuid.uuid4().hex
        hubmap_id = self.hmidGen()

        with self.lock:
            count = 0
            while(self.uuidExists(uuid) and count < 100):
                uuid = self.uuidGen() #uuid.uuid4().hex
                count = count + 1
            if count == 100:
                raise Exception("Unable to generate a unique uuid after 100 attempts")

            count = 0;
            while(self.doiExists(hubmap_id) and count < 100):
                hubmap_id = self.hmidGen()
                count = count + 1
            if count == 100:
                raise Exception("Unable to generate a unique hubmap id after 100 attempts")                 
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            sql = "INSERT INTO hm_uuids (HMUUID, DOI_SUFFIX, ENTITY_TYPE, PARENT_UUID, TIME_GENERATED, USER_ID, USER_EMAIL, HUBMAP_ID)
             VALUES (%s, %s, %s, %s, %s, %s,%s, %s)"
            vals = (uuid, hubmap_id, entityType, parentID, now, userId, userEmail, submissionId)
            with closing(self.hmdb.getDBConnection()) as dbConn:
                with closing(dbConn.cursor()) as curs:
                    curs.execute(sql, vals)
                dbConn.commit()

        disp_hubmap_id = self.__displayDoi(hubmap_id)
        if submissionId is None:
            rVal = {
                "displayDoi": disp_hubmap_id,
                "doi": hubmap_id,
                "uuid": uuid
                }
        else:
            rVal = {
                "displayDoi": disp_hubmap_id,
                "doi": hubmap_id,
                "uuid": uuid,
                "hubmapId": submissionId
                }               
        return rVal

'''
