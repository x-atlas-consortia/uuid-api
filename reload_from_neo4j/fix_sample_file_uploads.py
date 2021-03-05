import traceback
from py2neo import Graph
from hubmap_commons.exceptions import ErrorMessage
from hubmap_commons.properties import PropHelper
from hubmap_commons import file_helper
from uuid_worker import UUIDWorker
import sys
import os
import json
import hashlib
import requests
from shutil import copyfile

SAMPLES_TO_FIX_Q = "match (s:Sample) where s.portal_metadata_upload_files is not null and not s.portal_metadata_upload_files = '[]' return s.uuid, s.portal_metadata_upload_files"

class FixFileUploads:
    
    def __init__(self, property_file_name):
        self.props = PropHelper(property_file_name, required_props = ['neo4j.server', 'neo4j.username', 'neo4j.password', 'db.host', 'db.name', 'db.username', 'db.password', 'user.mapping', 'client.id', 'client.secret', 'old.ingest.upload.dir', 'new.ingest.upload.dir', 'uuid.api.url', 'user.nexus.token'])
        self.graph = Graph(self.props.get('neo4j.server'), auth=(self.props.get('neo4j.username'), self.props.get('neo4j.password')))
        self.uuid_wrker = UUIDWorker(self.props.get('client.id'), self.props.get('client.secret'), self.props.get('db.host'), self.props.get('db.name'), self.props.get('db.username'), self.props.get('db.password'))
        self.old_ingest_upload_dir = file_helper.ensureTrailingSlash(self.props.get('old.ingest.upload.dir'))
        self.new_ingest_upload_dir = file_helper.ensureTrailingSlash(self.props.get('new.ingest.upload.dir'))
        self.uuid_api_url = file_helper.ensureTrailingSlashURL(self.props.get('uuid.api.url')) + "hmuuid"
        self.user_token = self.props.get('user.nexus.token')
        
    def fix_sample_file_uploads(self):
        samples = self.graph.run(SAMPLES_TO_FIX_Q).data()
        tofix = []
        for sample in samples:
            uuid = sample['s.uuid']
            file_json = sample['s.portal_metadata_upload_files'].replace("'", '"')
            file_info = json.loads(file_json)
            changes = {"uuid":uuid, "changes":[]}
            tofix.append(changes)
            for fi in file_info:
                change_info = {}
                file_path = fi['filepath']
                dirs = file_path.split('/')
                n_dirs = len(dirs)
                old_rel_dir = dirs[n_dirs-3] + os.sep + dirs[n_dirs-2]
                
                change_info['copy_from'] = self.old_ingest_upload_dir + old_rel_dir + os.sep + dirs[n_dirs-1]
                if not os.path.exists(change_info['copy_from']):
                    raise Exception(f'File {change_info["copy_from"]} attached to entity with uuid:{uuid} does not exist')
                change_info['file_uuid'] = self.__gen_file_uuid(change_info['copy_from'], uuid + os.sep + '<uuid>' + os.sep + dirs[n_dirs-1], uuid)
                new_rel_dir = uuid + os.sep + change_info['file_uuid']
                new_rel_path = new_rel_dir + os.sep + dirs[n_dirs-1]
                change_info['copy_to'] = self.new_ingest_upload_dir + new_rel_path
                change_info['file_path'] = new_rel_path
                change_info['file_name'] = dirs[n_dirs-1]
                if not os.path.exists(self.new_ingest_upload_dir + new_rel_dir):
                    os.makedirs(self.new_ingest_upload_dir + new_rel_dir)
                description = ""
                if 'description' in fi:
                    change_info['description'] = fi['description']
                changes['changes'].append(change_info)

        for fix_rcd in tofix:
            uuid = fix_rcd['uuid']
            new_files_recd = []
            for change in fix_rcd['changes']:
                print(f'copy {change["copy_from"]} to {change["copy_to"]}')
                file_rcd = {}
                file_rcd['filename'] = change['file_name']
                file_rcd['file_uuid'] = change['file_uuid']
                if 'description' in change:
                    file_rcd['description'] = change['description']
                new_files_recd.append(file_rcd)
                copyfile(change["copy_from"], change["copy_to"])
            
            #update the record
            update_cql = "match (s:Sample {uuid:'" + uuid + "'}) set s.metadata_files = '" + json.dumps(new_files_recd) + "' return s.uuid"
            self.graph.run(update_cql)
            #print(uuid + ":" + json.dumps(new_files_recd))
            #if file_path
            #print(f"{uuid}:{file_json}")
    
    def __gen_file_uuid(self, file_current_path, file_rel_path, parent_entity_uuid):
        checksum = hashlib.md5(open(file_current_path, 'rb').read()).hexdigest()
        filesize = os.path.getsize(file_current_path)
        headers = {'Authorization': 'Bearer ' + self.user_token, 'Content-Type': 'application/json'}
        data = {}
        data['entity_type'] = 'FILE'
        data['parent_ids'] = [parent_entity_uuid]
        file_info= {}
        file_info['path'] = file_rel_path
        file_info['checksum'] = checksum
        file_info['base_dir'] = 'INGEST_PORTAL_UPLOAD'
        file_info['size'] = filesize
        data['file_info'] = [file_info]
        response = requests.post(self.uuid_api_url, json = data, headers = headers, verify = False)
        if response is None or response.status_code != 200:
            raise Exception(f"Unable to generate uuid for file {file_rel_path}")
        
        rsjs = response.json()
        file_uuid = rsjs[0]['uuid']
        return  file_uuid
        
        
    def tfix(self):
        samples = self.graph.run("match (s:Sample) where not s.metadata_files is null return s.uuid, s.metadata_files").data()
        for sample in samples:
            uuid = sample['s.uuid']
            file_json = sample['s.metadata_files'].replace("'", '"')
            file_info_arry = json.loads(file_json)
            replace_arry = []
            for file_info in file_info_arry:
                if 'file_path' in file_info:
                    f_path = file_info['file_path']
                    s_path = f_path.split('/')
                    file_info['filename'] = s_path[3]
                    print(file_info['filename'])
                    file_info.pop('file_path')
                replace_arry.append(file_info)
            update_cql = "match (s:Sample {uuid:'" + uuid + "'}) set s.metadata_files = '" + json.dumps(replace_arry) + "' return s.uuid"
            self.graph.run(update_cql)
    
try:
    fixer = FixFileUploads(os.path.dirname(os.path.realpath(__file__)) + "/reload.properties")
    fixer.fix_sample_file_uploads()

except ErrorMessage as em:                                                                                                            
    print(em.get_message())
    exit(1)    
except Exception as e:                                                                                                            
    exc_type, exc_value, exc_traceback = sys.exc_info()
    eMsg = str(e)                                                                                                                     
    print("ERROR Occurred: " + eMsg)
    traceback.print_tb(exc_traceback)
    exit(1)

        