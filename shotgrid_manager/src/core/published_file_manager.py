from core.base_manager import BaseManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging
from typing import List, Tuple
import logging


class PublishedFileManager(BaseManager):
    entity = "PublishedFile"
    entity_fields =  [
            'code','name', 'sg_status_list', 'created_at', 'project', 'id', 'description'
            'entity', 'entity.sg_asset_type', 'entity.sg_shot_type', 'version','task',
        ]
    
    def get_published_file(self, published_file_id:int)->dict:
        return self.get_entity(
            filters=[["id", "is", published_file_id]],
            fields=self.entity_fields
        )
    
    def get_published_files_from_task(self, task_id)->List[dict]:
        filters = [["task", "is", {"type":"Task", 'id': task_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)

    def get_published_files_from_version(self, version_id)->List[dict]:
        filters = [["task", "is", {"type":"Version", 'id': version_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)
    
    def get_published_files_from_project(self, project_id)->List[dict]:
        filters = [["project", "is", {"type":"Project", "id":project_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)
    
    def create_published_file(self, version_id:int, version_number:int, task_id, name:str, file_code:str, project_id:int, description:str="")->tuple[dict, dict]:
        published_file = self.create_entity(
            data= {
                "project":{"type":"Project", "id":project_id},
                "version":{"type":"Version", "id":version_id},
                "version_number":version_number,
                "task":{"type":"Task", "id":task_id},
                "name":name,
                "code":file_code,
                "description":description,
            }
        )
        return published_file
    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    published_file_manager = PublishedFileManager(shotgun_instance=flow)

    flow.connect()     
    data = published_file_manager.get_published_file( published_file_id=77)
    flow.disconnect()
    # data = version_manager.update_version(version_id=6990, data=_data)
    # logger.info(f"published_file: {published_file}")
    logger.info(f"upload_file= {data}")

    # upload_file= {
    #     'type': 'PublishedFile', 'id': 77, 'code': 'CianLu_V02.v004', 'name': 'generic_prop_1_002_Modeling_v004', 
    #     'sg_status_list': 'wtg', 
    #     'created_at': datetime.datetime(2025, 11, 28, 15, 10, 18, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x74c158c1f6d0>), 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'entity': None, 
    #     'version': {'id': 7031, 'name': 'generic_prop_1_002_Modeling_v004', 'type': 'Version'}, 
    #     'task': {'id': 5947, 'name': '002_Modeling', 'type': 'Task'}}