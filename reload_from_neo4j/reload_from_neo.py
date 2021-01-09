#Standalone script to reload, from scratch, the UUID relational database
#This script reads all Nodes in a HuBMAP Neo4j database and stores all id
#information in the UUID database

import traceback
from py2neo import Graph
from hubmap_commons.exceptions import ErrorMessage
from hubmap_commons.properties import PropHelper
import sys
import os
import json
from hmdb import DBConn
from uuid_worker import UUIDWorker
from contextlib import closing
import mysql
from datetime import datetime

# HuBMAP commons
from hubmap_commons.string_helper import isBlank
from hubmap_commons import globus_groups

# Deprecate the use of Provenance
#from hubmap_commons.provenance import Provenance

UUID_DB_TABLE_NAMES = ['hm_uuids', 'hm_ancestors', 'hm_organs', 'hm_data_centers']
LABS_CYPHER = "match (l:Lab) return l.uuid as labid, l.next_identifier, l.submission_id as lab_code"
DONORS_CYPHER = "match (d:Donor {entity_class:'Donor'})<-[:ACTIVITY_OUTPUT]-(a)-[:ACTIVITY_INPUT]-(lab:Lab) return d.uuid, d.submission_id, d.doi_suffix_id, d.hubmap_id, lab.uuid, d.created_by_user_email, d.created_timestamp, d.created_by_user_displayname, d.created_by_user_sub"
SAMPLES_CYPHER = "match (s:Sample {entity_class:'Sample'})<-[:ACTIVITY_OUTPUT]-(a)-[:ACTIVITY_INPUT]-(anc:Entity) return s.uuid, s.submission_id, s.doi_suffix_id, s.hubmap_id, anc.uuid, s.created_by_user_email, s.created_timestamp, s.created_by_user_displayname, s.created_by_user_sub, s.organ, s.specimen_type"
DATASETS_CYPHER = "match (ds:Dataset {entity_class:'Dataset'})<-[:ACTIVITY_OUTPUT]-(a)-[:ACTIVITY_INPUT]-(anc:Entity) return collect(anc.uuid) as ancestor_ids, ds.uuid, ds.doi_suffix_id, ds.hubmap_id, ds.created_by_user_email, ds.created_timestamp, ds.created_by_user_displayname, ds.created_by_user_sub"
ACTIVITIES_CYPHER = "match (a:Activity) return a.uuid, a.doi_suffix_id, a.hubmap_id, a.created_by_user_email, a.created_timestamp, a.created_by_user_displayname, a.created_by_user_sub"
COLLECTIONS_CYPHER = "match (c:Collection)<-[:IN_COLLECTION]-(ds:Dataset) return c.uuid, c.doi_suffix_id, c.hubmap_id, c.created_by_user_email, c.created_timestamp, c.created_by_user_displayname, c.created_by_user_sub, collect(ds.created_by_user_email) as ds_created_by_user_email, collect(ds.created_timestamp) as ds_created_timestamp, collect(ds.created_by_user_displayname) as ds_created_by_user_displayname, collect(ds.created_by_user_sub) as ds_created_by_user_sub"

def hubmap_timestamp_to_mysql(hm_timestamp):
    timestamp = datetime.fromtimestamp(int(hm_timestamp/1000) + 14400)
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def contains_attrib(dict, attrib_name):
    if attrib_name in dict and not dict[attrib_name] is None:
        t_val = dict[attrib_name]
        if isinstance(t_val, str):
            return not t_val.strip == ''
        return True
    else:
        return False

class ReloadUUIDFromNeo4j:
    
    def __init__(self, property_file_name):
        self.props = PropHelper(property_file_name, required_props = ['neo4j.server', 'neo4j.username', 'neo4j.password', 'db.host', 'db.name', 'db.username', 'db.password', 'user.mapping', 'client.id', 'client.secret'])
        self.graph = Graph(self.props.get('neo4j.server'), auth=(self.props.get('neo4j.username'), self.props.get('neo4j.password')))
        self.uuid_db = DBConn(self.props.get('db.host'), self.props.get('db.username'), self.props.get('db.password'), self.props.get('db.name'))
        user_mapping_json = self.props.get('user.mapping')
        self.user_mapping = json.loads('{' + user_mapping_json + '}')
        self.organs = {}
        self.record_count = 0
        self.count_page = 50
        self.uuid_wrker = UUIDWorker(self.props.get('client.id'), self.props.get('client.secret'), self.props.get('db.host'), self.props.get('db.name'), self.props.get('db.username'), self.props.get('db.password'))
        self.gened_uuids = []
        
    def clear_tables(self):
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for db_name in UUID_DB_TABLE_NAMES:
                    sql = "delete from " + db_name
                    curs.execute(sql)
                    db_conn.commit()
        
    def load_lab_info(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        labs = self.graph.run(LABS_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                count = 0
                for lab in labs:
                    self.record_counter()
                    count = count + 1
                    hm_id = 'TEMP' + str(count)
                    donor_count = int(lab['l.next_identifier']) - 1
                    sql = "insert into hm_data_centers (HM_UUID, DC_UUID, DC_CODE) VALUES ('" + hm_id + "', '" + lab['labid'].lower().strip() + "', '" + lab['lab_code'].upper().strip() + "')"
                    curs.execute(sql)
                    #'," + str(donor_count) + ",'
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, DESCENDANT_COUNT, TIME_GENERATED, USER_ID, USER_EMAIL) VALUES ('" + hm_id + "', 'LAB'," + str(donor_count) + ",'" + str_now + "','3e7bce63-129d-33d0-8f6c-834b34cd382e','hubmap@hubmapconsortium.org')"
                    curs.execute(sql)
                db_conn.commit()

    def load_donor_info(self):
        donors = self.graph.run(DONORS_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for donor in donors:
                    self.record_counter()                    
                    hm_uuid = donor['d.uuid']
                    base_id = donor['d.doi_suffix_id']
                    time_generated = hubmap_timestamp_to_mysql(donor['d.created_timestamp'])
                    user_name = donor['d.created_by_user_displayname']
                    user_id = donor['d.created_by_user_sub']
                    user_email = donor['d.created_by_user_email']
                    submission_id = donor['d.submission_id']
                    lab_id = donor['lab.uuid']
                    lab_uuid = self.get_lab_uuid(lab_id)
                    if lab_uuid is None:
                        raise Exception("No lab id found matching lab id:" + lab_id + " for donor with uuid:" + hm_uuid)
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, HUBMAP_BASE_ID, TIME_GENERATED, USER_ID, USER_EMAIL, SUBMISSION_ID) VALUES ('" + hm_uuid + "','DONOR','" + base_id + "', '" + time_generated + "', '" + user_id + "', '" + user_email + "', '" + submission_id + "')"
                    curs.execute(sql)
                    sql = "insert into hm_ancestors (ANCESTOR_UUID, DESCENDANT_UUID) VALUES ('" + lab_uuid + "', '" + hm_uuid + "')"
                    curs.execute(sql)
                db_conn.commit()


    def load_sample_info(self):
        samples = self.graph.run(SAMPLES_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for sample in samples:
                    self.record_counter()
                    hm_uuid = sample['s.uuid']
                    base_id = sample['s.doi_suffix_id']
                    time_generated = hubmap_timestamp_to_mysql(sample['s.created_timestamp'])
                    user_name = sample['s.created_by_user_displayname']
                    user_id = sample['s.created_by_user_sub']
                    user_email = sample['s.created_by_user_email']
                    submission_id = sample['s.submission_id']                    
                    ancestor_uuid = sample['anc.uuid']
                    sample_type = sample['s.specimen_type']
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, HUBMAP_BASE_ID, TIME_GENERATED, USER_ID, USER_EMAIL, SUBMISSION_ID) VALUES ('" + hm_uuid + "','SAMPLE','" + base_id + "', '" + time_generated + "', '" + user_id + "', '" + user_email + "', '" + submission_id + "')"
                    curs.execute(sql)
                    sql = "insert into hm_ancestors (ANCESTOR_UUID, DESCENDANT_UUID) VALUES ('" + ancestor_uuid + "', '" + hm_uuid + "')"
                    curs.execute(sql)
                    if contains_attrib(sample, 's.organ') and sample_type == 'organ':
                        self.track_organ(sample['s.organ'], ancestor_uuid, hm_uuid)
                self.write_organ_info(curs)
                db_conn.commit()
    
    def write_organ_info(self, db_curs):
        for donor_uuid in self.organs:
            for organ_code in self.organs[donor_uuid]:
                if organ_code == 'LY':
                    idx = self.organs[donor_uuid][organ_code]
                    sql = "insert into hm_organs (DONOR_UUID, ORGAN_CODE, ORGAN_COUNT) VALUES ('" + donor_uuid + "','LY'," + str(idx) + ")"
                else:
                    sql = "insert into hm_organs (DONOR_UUID, ORGAN_CODE, ORGAN_COUNT) VALUES ('" + donor_uuid + "','" + organ_code + "', 1)"
                db_curs.execute(sql)
                
    def track_organ(self, organ_code, donor_uuid, sample_uuid):
        code = organ_code
        idx = 1
        if organ_code[:2] == 'LY':
            code = 'LY'
            idx = int(organ_code[2:])
        
        if not donor_uuid in self.organs:
            self.organs[donor_uuid] = {code:idx}
        else:
            organ_info = self.organs[donor_uuid]
            if not code in organ_info:
                self.organs[donor_uuid][code] = idx
            elif not code == 'LY':
                raise Exception("donor with uuid:" + donor_uuid + " contains multiple organs of type " + code)
        if code == 'LY':
            if idx is None or not isinstance(idx, int):
                raise Exception("donor with uuid:" + donor_uuid + " has a descendant organ of type LY without an index")
            count = self.organs[donor_uuid][code]
            if idx > count:
                self.organs[donor_uuid][code] = idx
        
            
    #take a lab id (Globus group uuid for the lab group in Globus)
    def get_lab_uuid(self, lab_id):        
        #db_conn = self.uuid_db.getDBConnection()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                sql = "select HM_UUID from hm_data_centers where DC_UUID = '" + lab_id + "'"                
                results = curs.execute(sql)
                r = curs.fetchone()
                if r is None or len(r) == 0:
                    return None
                else:
                    return r[0]

    def load_dataset_info(self):
        datasets = self.graph.run(DATASETS_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for dataset in datasets:
                    self.record_counter()
                    hm_uuid = dataset['ds.uuid']
                    base_id = dataset['ds.doi_suffix_id']
                    time_generated = hubmap_timestamp_to_mysql(dataset['ds.created_timestamp'])
                    user_name = dataset['ds.created_by_user_displayname']
                    user_id = dataset['ds.created_by_user_sub']
                    user_email = dataset['ds.created_by_user_email']
                    ancestor_uuids = dataset['ancestor_ids']
                    if user_id is None:
                        user_id = self.get_user_id(user_email)
                        print("CHECK: Neo4j Dataset with uuid:" + hm_uuid + " missing created_by_user_sub should be " + user_id)
                            
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, HUBMAP_BASE_ID, TIME_GENERATED, USER_ID, USER_EMAIL) VALUES ('" + hm_uuid + "','DATASET','" + base_id + "', '" + time_generated + "', '" + user_id + "', '" + user_email + "')"
                    curs.execute(sql)
                    for ancestor_id in ancestor_uuids:
                        sql = "insert into hm_ancestors (ANCESTOR_UUID, DESCENDANT_UUID) VALUES ('" + ancestor_id + "', '" + hm_uuid + "')"
                        curs.execute(sql)
                db_conn.commit()

    def get_user_id(self, user_email):
        if user_email in self.user_mapping:
            return(self.user_mapping[user_email])
        else:
            raise Exception("User with email " + user_email + " not found in user email to mapping config")

    def load_activity_info(self):
        activities = self.graph.run(ACTIVITIES_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for activity in activities:
                    self.record_counter()
                    hm_uuid = activity['a.uuid']
                    base_id = activity['a.doi_suffix_id']
                    time_generated = hubmap_timestamp_to_mysql(activity['a.created_timestamp'])
                    user_name = activity['a.created_by_user_displayname']
                    user_id = activity['a.created_by_user_sub']
                    user_email = activity['a.created_by_user_email']
                    if user_id is None:
                        user_id = self.get_user_id(user_email)
                        print("CHECK: Neo4j Activity with uuid:" + hm_uuid + " missing created_by_user_sub should be " + user_id)
                    if base_id is None:
                        print("WARNING: Activity with uuid:" + hm_uuid + " was skipped, base DOI/HUBMAP id not set")
                        continue
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, HUBMAP_BASE_ID, TIME_GENERATED, USER_ID, USER_EMAIL) VALUES ('" + hm_uuid + "','ACTIVITY','" + base_id + "', '" + time_generated + "', '" + user_id + "', '" + user_email + "')"
                    curs.execute(sql)
                db_conn.commit()
 
    def load_collection_info(self):
        collections = self.graph.run(COLLECTIONS_CYPHER).data()
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                for collection in collections:
                    self.record_counter()
                    hm_uuid = collection['c.uuid']
                    base_id = collection['c.doi_suffix_id']
                    time_generated_int = self.get_collection_attrib(collection, "created_timestamp")
                    time_generated = hubmap_timestamp_to_mysql(time_generated_int)
                    user_name = self.get_collection_attrib(collection, 'created_by_user_displayname')
                    user_id = self.get_collection_attrib(collection, 'created_by_user_sub')
                    user_email = self.get_collection_attrib(collection, 'created_by_user_email')
                    sql = "insert into hm_uuids (HM_UUID, ENTITY_TYPE, HUBMAP_BASE_ID, TIME_GENERATED, USER_ID, USER_EMAIL) VALUES ('" + hm_uuid + "','COLLECTION','" + base_id + "', '" + time_generated + "', '" + user_id + "', '" + user_email + "')"
                    curs.execute(sql)
                db_conn.commit() 

    def get_collection_attrib(self, collection, attrib_name):
        collection_attrib_name = 'c.' + attrib_name
        if contains_attrib(collection, collection_attrib_name):
            return collection[collection_attrib_name]
        else:
            dataset_attrib_name = 'ds_' + attrib_name
            return collection[dataset_attrib_name][0]
    
    def record_counter(self):
        self.record_count = self.record_count + 1
        #if self.record_count % self.count_page == 0:
        #    print('.', end='', flush=True)

    def replace_temp_uuids(self):
        with closing(self.uuid_db.getDBConnection()) as db_conn:
            with closing(db_conn.cursor()) as curs:
                sql = "select hm_uuid from hm_uuids where hm_uuid like 'TEMP%'"
                curs.execute(sql)
                results = curs.fetchall()
                for rcd in results:
                    new_uuid = self.newUUID()
                    sql = "update hm_uuids set hm_uuid = '" + new_uuid + "' where hm_uuid = '" + rcd[0] + "'"
                    curs.execute(sql)
                    sql = "update hm_ancestors set ancestor_uuid = '" + new_uuid + "' where ancestor_uuid = '" + rcd[0] + "'"
                    curs.execute(sql)
                    sql = "update hm_data_centers set hm_uuid = '" + new_uuid + "' where hm_uuid = '" + rcd[0] + "'"
                    curs.execute(sql)
                db_conn.commit()
                
    def newUUID(self):
        hmid = self.uuid_wrker.uuidGen()
        count = 0
        while( (hmid in self.gened_uuids or self.uuid_wrker.uuid_exists(hmid)) and count < 100):
            hmid = self.uuid_wrker.uuidGen() #uuid.uuid4().hex
            count = count + 1
        if count == 100:
            raise Exception("Unable to generate a unique uuid after 100 attempts")
        self.gened_uuids.append(hmid)
        return(hmid)
    
    def convert_ancestor_array(self, results):
        
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
                    raise Exception("Unknown ancestor type")                
            else:
                raise Exception("Multiple results exist for a single id.")

        return record
    
    
    def test(self, lab_id):
        if isBlank(lab_id):
            return None
        check_id = lab_id.strip().lower()
        
        with closing(self.uuid_db.getDBConnection()) as dbConn:
            with closing(dbConn.cursor()) as curs:
                curs.execute("select hm_uuid from hm_data_centers where hm_uuid = '" + check_id + "' or dc_uuid = '" + check_id + "'")
                result = curs.fetchone()
                if result is None:
                    prov_helper = Provenance("a", "b", "c")
                    try:
                        # Deprecate the use of Provenance, use the new globus_groups module - Zhou
                        #lab = prov_helper.get_group_by_identifier(check_id)

                        # Get the globus groups info based on the groups json file in commons package
                        globus_groups_info = globus_groups.get_globus_groups_info()
                        groups_by_tmc_prefix_dict = globus_groups_info['by_tmc_prefix']
                        lab = groups_by_tmc_prefix_dict[check_id]
                    except ValueError:
                        return Response("")
                    if not 'tmc_prefix' in lab:
                        return Response("")
                    curs.execute("")
                    return(lab['tmc_prefix'])
                else:
                    return result[0]
try:
    reloader = ReloadUUIDFromNeo4j(os.path.dirname(os.path.realpath(__file__)) + "/reload.properties")
    reloader.clear_tables()
    print("Loading labs.", end='')
    reloader.load_lab_info()
    print("\nLoading donors.", end='')
    reloader.load_donor_info()
    print("\nLoading samples.", end='')
    reloader.load_sample_info()
    print("\nLoading datasets.", end='')
    reloader.load_dataset_info()
    print("\nLoading activities.", end='')
    reloader.load_activity_info()
    print("\nLoading collections.", end='')
    reloader.load_collection_info()
    print("\nReplacing temp UUIDs")
    reloader.replace_temp_uuids()
    #print(reloader.test('2cf25858-ed44-11e8-991d-0e368f3075e8Z'))
    
except ErrorMessage as em:                                                                                                            
    print(em.get_message())
    exit(1)    
except Exception as e:                                                                                                            
    exc_type, exc_value, exc_traceback = sys.exc_info()
    eMsg = str(e)                                                                                                                     
    print("ERROR Occurred: " + eMsg)
    traceback.print_tb(exc_traceback)
    exit(1)

    