import logging
from flask import Response
import threading
import secrets
import time
from contextlib import closing
import json
from hmdb import DBConn
import copy

# HuBMAP commons
from hubmap_commons.string_helper import isBlank, listToCommaSeparated, padLeadingZeros
from hubmap_commons.hm_auth import AuthHelper
from hubmap_commons import globus_groups

# Deprecate the use of Provenance
#from hubmap_commons.provenance import Provenance

BASE_DIR_TYPES = ['DATA_UPLOAD', 'INGEST_PORTAL_UPLOAD']

HUBMAP_ID_ENTITY_TYPES = ['ACTIVITY', 'SAMPLE', 'DONOR', 'DATASET', 'COLLECTION']
SUBMISSION_ID_ENTITY_TYPES = ['SAMPLE', 'DONOR']
ANCESTOR_REQUIRED_ENTITY_TYPES = ['SAMPLE', 'DONOR', 'DATASET', 'FILE']

MULTIPLE_ALLOWED_ORGANS = ['LY', 'SK']

MAX_GEN_IDS = 200
INSERT_SQL = "INSERT INTO hm_uuids (HM_UUID, HUBMAP_BASE_ID, ENTITY_TYPE, TIME_GENERATED, USER_ID, USER_EMAIL) VALUES (%s, %s, %s, %s, %s, %s)"
INSERT_SQL_WITH_SUBMISSION_ID = "INSERT INTO hm_uuids (HM_UUID, HUBMAP_BASE_ID, ENTITY_TYPE, TIME_GENERATED, USER_ID, USER_EMAIL, SUBMISSION_ID) VALUES (%s, %s, %s, %s, %s, %s,%s)"
INSERT_ANCESTOR_SQL = "INSERT INTO hm_ancestors (DESCENDANT_UUID, ANCESTOR_UUID) VALUES (%s, %s)"
INSERT_FILE_INFO_SQL = "INSERT INTO hm_files (HM_UUID, PATH, CHECKSUM, SIZE, BASE_DIR) VALUES (%s, %s, %s, %s, %s)"
#INSERT_FILE_INFO_SQL = "INSERT INTO hm_files (HM_UUID, PATH, CHECKSUM) VALUES (%s, %s, %s)"
#UPDATE_SQL = "UPDATE hm_uuids set hubmap_id = %s where HMUUID = %s"

HMID_ALPHA_CHARS=['B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Z']                 
HMID_NUM_CHARS=['2','3','4','5','6','7','8','9']                                                                                   
HEX_CHARS=['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
#UUID_SELECTS = "HMUUID as hmuuid, DOI_SUFFIX as doiSuffix, ENTITY_TYPE as type, PARENT_UUID as parentId, TIME_GENERATED as timeStamp, USER_ID as userId, HUBMAP_ID as hubmapId, USER_EMAIL as email"
UUID_SELECTS = "HM_UUID as hm_uuid, HUBMAP_BASE_ID as hubmap_base_id, ENTITY_TYPE as type, TIME_GENERATED as time_generated, USER_ID as user_id, SUBMISSION_ID as submission_id, USER_EMAIL as email, GROUP_CONCAT(ancestor_uuid) as ancestor_ids"

def startsWithComponentPrefix(hmid):
    tidl = hmid.strip().lower()
    if tidl.startswith('test') or tidl.startswith('van') or tidl.startswith('ufl') or tidl.startswith('stan') or tidl.startswith('ucsd') or tidl.startswith('calt') or tidl.startswith('rtibd') or tidl.startswith('rtige') or tidl.startswith('rtinw') or tidl.startswith('rtist') or tidl.startswith('ttdct') or tidl.startswith('ttdhv') or tidl.startswith('ttdpd') or tidl.startswith('ttdst'):
        return True
    else:
        return False


def isValidHMId(hmid):
    if isBlank(hmid): return False
    if  startsWithComponentPrefix(hmid):
        return True 
    tid = stripHMid(hmid)
    l = len(tid)
    if not (l == 10 or l == 32): return False
    tid = tid.upper()
    if l == 10:
        if not set(tid[0:3]).issubset(HMID_NUM_CHARS): return False
        if not set(tid[3:7]).issubset(HMID_ALPHA_CHARS): return False
        if not set(tid[7:]).issubset(HMID_NUM_CHARS): return False
    if l == 32:
        if not set(tid).issubset(HEX_CHARS): return False
    return True

def stripHMid(hmid):
    if isBlank(hmid): return hmid
    thmid = hmid.strip();
    if thmid.lower().startswith('hbm'): thmid = thmid[3:]
    if thmid.startswith(':'): thmid = thmid[1:]
    return  thmid.strip().replace('-', '').replace('.', '').replace(' ', '')


class UUIDWorker:

    authHelper = None
    
    def __init__(self, clientId, clientSecret, dbHost, dbName, dbUsername, dbPassword):
        if clientId is None or clientSecret is None or isBlank(clientId) or isBlank(clientSecret):
            raise Exception("Globus client id and secret are required in AuthHelper")

        if not AuthHelper.isInitialized():
            self.authHelper = AuthHelper.create(clientId=clientId, clientSecret=clientSecret)
        else:
            self.authHelper.instance()
            
        #Open the config file   
        self.logger = logging.getLogger('uuid.service')                                                                                                                                                                                                  

        self.dbHost = dbHost
        self.dbName = dbName
        self.dbUsername = dbUsername
        self.dbPassword = dbPassword
        self.lock = threading.RLock()
        self.hmdb = DBConn(self.dbHost, self.dbUsername, self.dbPassword, self.dbName)
        
        # Deprecate the use of Provenance
        #self.prov_helper = Provenance(clientId, clientSecret, None)

    def __resolve_lab_id(self, lab_id, user_id, user_email):
        if isBlank(lab_id):
            return None
        check_id = lab_id.strip().lower()
        r_val = {}
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select hm_uuid, dc_code from hm_data_centers where hm_uuid = '" + check_id + "' or dc_uuid = '" + check_id + "'")
                result = curs.fetchone()
                if result is None:
                    try:
                        # Deprecate the use of Provenance
                        #lab = self.prov_helper.get_group_by_identifier(check_id)

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

                    uuid_json = self.newUUIDs([], "LAB", user_id, user_email, 1, gen_base_ids = False)
                    uuid_info = json.loads(uuid_json)
                    r_val['dc_code'] = lab['tmc_prefix']
                    r_val['hm_uuid'] = uuid_info[0]['uuid']
                    curs.execute("insert into hm_data_centers (HM_UUID, DC_UUID, DC_CODE) VALUES ('" + r_val['hm_uuid'] + "','" + check_id + "','" + r_val['dc_code'] + "')")
                    dbConn.commit()
                else:
                    r_val['dc_code'] = result[1]
                    r_val['hm_uuid'] = result[0]
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
            return(Response("Invalid input, json required.", 400))
        content = req.get_json()
        if content is None or len(content) <= 0:
            return(Response("Invalid input, uuid attributes required", 400))
        if not 'entity_type' in content or isBlank(content['entity_type']):
            return(Response("entity_type is a required attribute", 400))
        
        entityType = content['entity_type'].upper().strip()
        organ_code = None
        if 'organ_code' in content and not isBlank(content['organ_code']):
            if not entityType == 'SAMPLE':
                return(Response("Organ code " + content['organ_code'] + " found for entity type of " + entityType + ", but SAMPLE entity type required to specify organ.", 400))
            organ_code = content['organ_code'].strip().upper()
            
        
        parentIds = None
        if('parent_ids' in content):
            parentIds = content['parent_ids']

        if(entityType in ANCESTOR_REQUIRED_ENTITY_TYPES and parentIds is None):
            return(Response("parentId is a required attribute for entities " + ", ".join(ANCESTOR_REQUIRED_ENTITY_TYPES), 400))

        lab_code = None
        
        if not parentIds is None:
            if(entityType in SUBMISSION_ID_ENTITY_TYPES):
                n_parents = len(parentIds)
                if n_parents != 1:
                    return(Response("Entity type " + entityType + " requires a single ancestor id, " + str(n_parents) + " provided.", 400))

        if entityType == "DONOR":
            ancestor_ids = []
            lab_info = self.__resolve_lab_id(parentIds[0], userId, userEmail)
            if isinstance(lab_info, Response):
                return lab_info
            ancestor_ids.append(lab_info['hm_uuid'])
            lab_code = lab_info['dc_code']
        elif parentIds is None:
            ancestor_ids = []
        else:
            ancestor_ids = parentIds
        
        file_info = None
        base_dir = None
        if entityType == "FILE":
            if not 'file_info' in content:
                return(Response("Entity type of FILE requires a file_info array provide in the request body.", 400))
            file_info = content['file_info']
            if not isinstance(file_info, list):
                return(Response("file_info attribute must be a list", 400))
            if not len(file_info) == nIds:
                return(Response("number file_info list must contain the same number of entries as ids being generated " + str(nIds)))
            for fi in file_info:
                if not 'path' in fi or isBlank(fi['path']):
                    return(Response("The 'path' attribute is required for each file_info entry", 400))
                if not 'base_dir' in fi or isBlank(fi['base_dir']):
                    return(Response("the 'base_dir' attribute is required for each file_info entity.  Valid values are " + " ".join(BASE_DIR_TYPES), 400))
                base_dir = fi['base_dir'].strip().upper()
                if not base_dir in BASE_DIR_TYPES:
                    return(Response("valid base_dir values are " + " ".join(BASE_DIR_TYPES)))
        for parentId in ancestor_ids:
            if not self.uuid_exists(parentId):
                return(Response("Parent id " + parentId + " does not exist", 400))

        return self.newUUIDs(ancestor_ids, entityType, userId, userEmail, nIds, organ_code = organ_code, lab_code = lab_code, file_info_array = file_info, base_dir_type = base_dir)

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

    def uuidGen(self):
        hexVal = ""
        for _ in range(32):                                                                                                                
            hexVal = hexVal + secrets.choice(HEX_CHARS)
        hexVal = hexVal.lower()
        return hexVal
    
    def __create_submission_ids(self, num_to_gen, parent_id, entity_type, organ_code = None, lab_code = None):
        parent_id = parent_id.strip().lower()
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select entity_type, descendant_count, submission_id from hm_uuids where hm_uuid = '" + parent_id + "'")
                results = curs.fetchone()
                anc_entity_type = results[0]
                desc_count = results[1]
                anc_submission_id = results[2]
                #a donor
                if entity_type == 'DONOR':
                    if not anc_entity_type == 'LAB': 
                        return Response("An id can't be created for a DONOR because a DATA CENTER is required as the direct ancestor and an ancestor of type " + anc_entity_type + " found.", 400)
                    if isBlank(lab_code):
                        return Response("No data center code found data center with uuid:" + parent_id + ". Unable to generate an id for a DONOR.", 400)
                    r_val = []
                    for _ in range(0, num_to_gen):
                        desc_count = desc_count + 1
                        r_val.append(lab_code.strip().upper() + padLeadingZeros(desc_count, 4))
                    curs.execute("update hm_uuids set descendant_count = " + str(desc_count) + " where hm_uuid = '" + parent_id + "'")
                    dbConn.commit()
                    return r_val
                #an organ
                elif entity_type == 'SAMPLE' and anc_entity_type == 'DONOR':
                    if isBlank(organ_code):
                        return Response("An id can't be created for a SAMPLE because the immediate ancestor is a DONOR and the SAMPLE was not supplied with an associated organ code (SAMPLE must be an organ to have a DONOR as a direct ancestor)", 400)
                    organ_code = organ_code.strip().upper()
                    curs.execute("select organ_count from hm_organs where donor_uuid = '" + parent_id + "' and organ_code = '" + organ_code + "'")
                    org_res = curs.fetchone()
                    if org_res is None:
                        curs.execute("insert into hm_organs (DONOR_UUID, ORGAN_CODE, ORGAN_COUNT) VALUE ('" + parent_id + "', '" + organ_code + "', 0)")
                        dbConn.commit()
                        org_count = 0
                    else:
                        org_count = org_res[0]
                    if not organ_code in MULTIPLE_ALLOWED_ORGANS:
                        if org_count >= 1:
                            return Response("Cannot add another organ of type " + organ_code + " to DONOR " + parent_id + " exists already.", 400)
                        if num_to_gen > 1:
                            return Response("Cannot create multiple submission ids for organ of type " + organ_code + ". " + str(num_to_gen) + " requested.")
                        org_count = 1
                        r_val = [anc_submission_id + "-" + organ_code]                  
                    else:
                        r_val = []
                        for _ in range(0, num_to_gen):
                            org_count = org_count + 1
                            r_val.append(anc_submission_id + "-" + organ_code + padLeadingZeros(org_count, 2))
                    
                    curs.execute("update hm_organs set organ_count = " + str(org_count) + " where donor_uuid = '" + parent_id + "' and organ_code = '" + organ_code + "'")
                    dbConn.commit()
                    return r_val
                
                #error if remaining non-organ samples are not the descendants of a SAMPLE           
                elif entity_type == 'SAMPLE' and not anc_entity_type == 'SAMPLE':
                    return Response("Cannot create a submission id for a SAMPLE with a direct ancestor of " + anc_entity_type)
                elif entity_type == 'SAMPLE':
                    r_val = []
                    for _ in range(0, num_to_gen):
                        desc_count = desc_count + 1
                        r_val.append(anc_submission_id + "-" + str(desc_count))
                    curs.execute("update hm_uuids set descendant_count = " + str(desc_count) + " where hm_uuid = '" + parent_id + "'")
                    dbConn.commit()
                    return r_val
                else:
                    return Response("Cannot create a submission id for an entity of type " + entity_type)
        
    #generate multiple ids, one for each display id in the displayIds array

    def newUUIDs(self, parentIDs, entityType, userId, userEmail, nIds, organ_code = None, lab_code = None, file_info_array = None, base_dir_type = None):
        #if entityType == 'DONOR':
        gen_base_ids = entityType in HUBMAP_ID_ENTITY_TYPES
        returnIds = []
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        store_file_info = False
        if entityType == 'FILE':
            store_file_info = True
        with self.lock:        
            #generate in batches
            previousUUIDs = set()
            previous_hubmap_ids = set()
            
            gen_submission_ids = False
            if entityType in SUBMISSION_ID_ENTITY_TYPES:
                gen_submission_ids = True
                
            for i in range(0, nIds, MAX_GEN_IDS):
                insertVals = []
                file_info_insert_vals = []
                insertParents = []
                numToGen = min(MAX_GEN_IDS, nIds - i)
                #generate uuids
                uuids = self.__nUniqueIds(numToGen, self.uuidGen, "HM_UUID", previousGeneratedIds=previousUUIDs)
                if gen_base_ids:
                    hubmap_base_ids = self.__nUniqueIds(numToGen, self.hmidGen, "HUBMAP_BASE_ID", previousGeneratedIds=previous_hubmap_ids)
                else:
                    hubmap_base_ids = [None] * numToGen

                count_increase_q = None
                submission_ids = None
                if gen_submission_ids:
                    submission_ids = self.__create_submission_ids(numToGen, parentIDs[0], entityType, organ_code = organ_code, lab_code = lab_code)
                    if isinstance(submission_ids, Response):
                        return submission_ids
                
                for n in range(0, numToGen):
                    insUuid = uuids[n]
                    previousUUIDs.add(insUuid)
                    thisId = {"uuid":insUuid}

                    if gen_base_ids:
                        ins_hubmap_base_id = hubmap_base_ids[n]
                        previous_hubmap_ids.add(ins_hubmap_base_id)
                        ins_display_hubmap_id = self.__display_hm_id(ins_hubmap_base_id)
                        thisId["hubmap_base_id"] = ins_hubmap_base_id
                        thisId["hubmap_id"] = ins_display_hubmap_id
                    else:
                        ins_hubmap_base_id = None
                        
                    if gen_submission_ids:
                        thisId["submission_id"] = submission_ids[n]
                        insRow = (insUuid, ins_hubmap_base_id, entityType, now, userId, userEmail, submission_ids[n])
                    else:
                        insRow = (insUuid, ins_hubmap_base_id, entityType, now, userId, userEmail)
                    
                    if store_file_info:
                        info_idx = i + n
                        file_path = file_info_array[info_idx]['path']
                        file_checksum = None
                        file_size = None
                        if 'checksum' in file_info_array[info_idx]:
                            file_checksum = file_info_array[info_idx]['checksum']
                        if 'size' in file_info_array[info_idx]:
                            file_size = file_info_array[info_idx]['size']
                        file_info_ins_row = (insUuid, file_path, file_checksum, file_size, base_dir_type)    
                        #file_info_ins_row = (insUuid, file_path, file_checksum)
                        file_info_insert_vals.append(file_info_ins_row)
                        thisId['file_path'] = file_path
                        
                    returnIds.append(thisId)
                    insertVals.append(insRow)

                    for parentId in parentIDs:
                        parRow = (insUuid, parentId)
                        insertParents.append(parRow)
        
                with closing(self.hmdb.getDBConnection()) as dbConn:
                    with closing(dbConn.cursor()) as curs:
                        if gen_submission_ids:
                            curs.executemany(INSERT_SQL_WITH_SUBMISSION_ID, insertVals)
                            curs.execute(count_increase_q)
                        else:
                            curs.executemany(INSERT_SQL, insertVals)
                        if store_file_info:
                            curs.executemany(INSERT_FILE_INFO_SQL, file_info_insert_vals)
                            
                        curs.executemany(INSERT_ANCESTOR_SQL, insertParents)
                    dbConn.commit()
            
        return json.dumps(returnIds)

    def nUniqueIds(self, nIds, idGenMethod, dbColumn):
        return self.__nUniqueIds(nIds, idGenMethod, dbColumn)
        
    #generate unique ids
    #generates ids with provided id generation method and checks them against existing ids in the DB
    #this method MUST BE CALLED FROM WITHIN a self.lock block
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
            replacements = self.__nUniqueIds(len(dupes), idGenMethod, dbColumn, previousGeneratedIds=lclPreviousIds, iteration=n_iter)
            for val in dupes:
                ids.remove(val[0])
            for val in replacements:
                ids.add(val)
        return list(ids)
    
    def __findDupsInDB(self, dbColumn, idSet):
        sql = "select " + dbColumn + " from hm_uuids where " + dbColumn + " IN(" + listToCommaSeparated(idSet, "'", True) + ")"
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute(sql)
                dupes = curs.fetchall()
        
        return dupes



    #which items in idSet are not in the database
    def __findExclusionsInDB(self, dbColumn, idSet):
        
        sql = "select " + dbColumn + " from ( "
        first = True
        for ex_id in idSet:
            if first: first = False
            else: sql = sql + " UNION ALL "
            sql = sql + "(select '" + ex_id + "' as " + dbColumn + ")"
        sql = sql + ") as list left join hm_uuids using (" + dbColumn + ") where hm_uuids." + dbColumn + " is null"
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute(sql)
                excluded = curs.fetchall()
        
        return excluded 

    def __display_hm_id(self, hm_base_id):
        hubmap_id = 'HBM' + hm_base_id[0:3] + '.' + hm_base_id[3:7] + '.' + hm_base_id[7:]
        return hubmap_id
        
    def hmidGen(self):
        nums1 = ''                                                                                                                        
        nums2 = ''                                                                                                                        
        alphs = ''                                                                                                                        
        for _ in range(3):                                                                                                                
            nums1 = nums1 + secrets.choice(HMID_NUM_CHARS) #[random.randint(0,len(DOI_NUM_CHARS)-1)]                                                           
        for _ in range(3):                                                                                                                
            nums2 = nums2 + secrets.choice(HMID_NUM_CHARS) #[random.randint(0,len(DOI_NUM_CHARS)-1)]                                                           
        for _ in range(4):                                                                                                                
            alphs = alphs + secrets.choice(HMID_ALPHA_CHARS) #[random.randint(0,len(DOI_ALPHA_CHARS)-1)]                                                       

        val = nums1 + alphs + nums2   
        return(val)
    
    def getIdExists(self, hmid):
            if not isValidHMId(hmid):
                return Response("Invalid HuBMAP Id", 400)
            tid = stripHMid(hmid)
            if startsWithComponentPrefix(hmid):         
                return self.submission_id_exists(hmid.strip())      
            elif len(tid) == 10:
                return self.base_id_exists(tid.upper())
            elif len(tid) == 32:
                return self.uuid_exists(tid.lower())
            else:
                return Response("Invalid HuBMAP Id (or empty or bad length)", 400)  

    
    #convert csv list of ancestor ids to a list
    #convert hubmap base id to a hubmap id (display version)
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
                
                if 'hubmap_base_id' in record:
                    if not record['hubmap_base_id'].strip() == '':
                        record['hubmap_id'] = self.__display_hm_id(record['hubmap_base_id'])
                    record.pop('hubmap_base_id', '')        
            else:
                raise Exception("Multiple results exist for id:" + hmid)
    
        return record
    
    def getIdInfo(self, hmid):
        if not isValidHMId(hmid):
            return Response(hmid + " is not a valid id format", 400)
        tidl = hmid.strip().lower()
        tid = stripHMid(hmid)
        if startsWithComponentPrefix(hmid):
            sql = "select " + UUID_SELECTS + " from hm_uuids inner join hm_ancestors on hm_ancestors.descendant_uuid = hm_uuids.hm_uuid where lower(submission_id) ='" + tidl + "'"
        elif len(tid) == 10:
            sql = "select " + UUID_SELECTS + " from hm_uuids inner join hm_ancestors on hm_ancestors.descendant_uuid = hm_uuids.hm_uuid where hubmap_base_id ='" + tid + "'"
        elif len(tid) == 32:
            sql = "select " + UUID_SELECTS + " from hm_uuids inner join hm_ancestors on hm_ancestors.descendant_uuid = hm_uuids.hm_uuid where hm_uuid ='" + tid + "'"
        else:
            return Response("Invalid id (empty or bad length)", 400)
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute(sql)
                results = [dict((curs.description[i][0], value) for i, value in enumerate(row)) for row in curs.fetchall()]

        # In Python, empty sequences (strings, lists, tuples) are false
        if results is None or not results:
            return Response ("Could not find the target id: " + hmid, 404)
        if isinstance(results, list) and (len(results) == 0):
            return Response ("Could not find the target id: " + hmid, 404)
        if not 'hm_uuid' in results[0]:
            return Response ("Could not find the target id: " + hmid, 404)
        if results[0]['hm_uuid'] is None:
            return Response ("Could not find the target id: " + hmid, 404)
        
        rdict = self._convert_result_id_array(results, hmid)
        return json.dumps(rdict, indent=4, sort_keys=True, default=str)
    
    def getFileIdInfo(self, fid):
        check_id = fid.strip()
        if isBlank(check_id) or len(check_id) != 32:
            return Response("Invalid file id format.  32 digit hex only.", 400)
        sql = "select hm_uuid, path, checksum, size, base_dir, ancestor_uuid from hm_files inner join hm_ancestors on hm_ancestors.descendant_uuid = hm_files.hm_uuid where hm_uuid = '" + check_id + "'"
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute(sql)
                results = [dict((curs.description[i][0], value) for i, value in enumerate(row)) for row in curs.fetchall()]
                
        if results is None or not results:
            return Response ("Could not find the target id: " + fid, 404)
        if isinstance(results, list) and (len(results) == 0):
            return Response ("Could not find the target id: " + fid, 404)
        if not 'hm_uuid' in results[0]:
            return Response ("Could not find the target id: " + fid, 404)
        if results[0]['hm_uuid'] is None:
            return Response ("Could not find the target id: " + fid, 404)
                    
        rdict = self._convert_result_id_array(results, check_id)
        if 'checksum' in rdict and rdict['checksum'] is None: rdict.pop('checksum')
        if 'size' in rdict and rdict['size'] is None: rdict.pop('size') 
        return json.dumps(rdict, indent=4, sort_keys=True, default=str)
                        
    def uuid_exists(self, hmid):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select count(*) from hm_uuids where hm_uuid = '" + hmid + "'")
                res = curs.fetchone()

        if(res is None or len(res) == 0): return False
        if(res[0] == 1): return True
        if(res[0] == 0): return False
        raise Exception("Multiple uuids found matching " + hmid)
    
#   def uuidsExist(self, uuids):
#       uuid_list = '('
#       first = True
#       comma = ''
#       for uuid in uuids:
#           uuid_list = uuid_list + comma + "'" + uuid.strip() + "'"
#           if first:
#               first = False
#               comma = ','
#       uuid_list = uuid_list + ')'
#
#       with closing(self.hmdb.getDBConnection()) as dbConn:
#           with closing(dbConn.cursor()) as curs:
#               curs.execute("select count(*) from hm_uuids where hm_uuid in " + uuid_list)
#               res = curs.fetchone()
#
#       if(res is None or len(res) == 0): return False
#       count = res[0]
#       if count != len(uuids): return False
#       return True
    
    def base_id_exists(self, base_id):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select count(*) from hm_uuids where hubmap_base_id = '" + base_id + "'")
                res = curs.fetchone()
        if(res is None or len(res) == 0): return False
        if(res[0] == 1): return True
        if(res[0] == 0): return False
        raise Exception("Multiple hubmap base ids found matching " + base_id)
        
    def submission_id_exists(self, hmid):
        with closing(self.hmdb.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select count(*) from hm_uuids where submission_id = '" + hmid + "'")
                res = curs.fetchone()
        if(res is None or len(res) == 0): return False
        if(res[0] == 1): return True
        if(res[0] == 0): return False
        raise Exception("Multiple HuBMAP IDs found matching " + hmid)

    def testConnection(self):
        try:
            res = None
            with closing(self.hmdb.getDBConnection()) as dbConn:
                with closing(dbConn.cursor()) as curs:
                    curs.execute("select 'ANYTHING'")
                    res = curs.fetchone()
            
            if(res is None or len(res) == 0): return False
            if(res[0] == 'ANYTHING'):
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(e, exc_info=True)
            return False

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
            sql = "INSERT INTO hm_uuids (HMUUID, DOI_SUFFIX, ENTITY_TYPE, PARENT_UUID, TIME_GENERATED, USER_ID, USER_EMAIL, HUBMAP_ID) VALUES (%s, %s, %s, %s, %s, %s,%s, %s)"
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
