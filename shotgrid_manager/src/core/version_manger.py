from core.base_manager import BaseManager
from utils.logger import setup_logging
from typing import List
import logging


class VersionManager(BaseManager):
    entity = "Version"
    entity_fields = ['tasks', 'id', 'sg_task', 'published_files', 'code', 'sg_status_list']

    def get_version(self, version_id:int)->dict:
        return self.get_entity(
            filters=[["id", "is", version_id]],
            fields=self.entity_fields
        )

    def get_versions_from_task(self, task_id:int)-> List[dict]:
        """
        returns a list of task dictionaries
        """
        version_list = self.get_entities(
            filters=[["sg_task", "is", {"type": "Task", "id":task_id}]], 
            fields=["id", "code", "client_code","entity", "created_at", "project", "tasks", "published_files"],
            order=[{'field_name':'created_at', 'direction':'desc'}]
        )

        return version_list
    
    def create_version(self, task_id:int, name:str, version_code:str, project_id:int)->dict:
        version = self.create_entity(
            data= {
                "project":{"type":"Project", "id":project_id},
                "sg_task":{"type":"Task", "id":task_id},
                "code":name,
                "client_code":version_code
            }
        )
        return version
    
    def update_version(self, version_id, data_to_update)->dict:

        updated_version = self.update_entity(
                entity_id=version_id,
                data=data_to_update
            )
        return updated_version
    
    def get_next_version_number_for_task(self, task_id:int)->int:
        """
        Determine next version number for task.

        Returns 1 if no versions exist, otherwise len(versions) + 1
        """
        try:
            versions = self.get_versions_from_task(task_id=task_id)
            version_count = len(versions) if versions else 0
            return version_count + 1

        except Exception as e:
            self.logger.warning(f"Error getting versions for task {task_id}: {e}")
            # Default to version 1 if we can't get version list
            return 1
    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    flow.connect()
    version_manager = VersionManager(shotgun_instance=flow)
    # _data = {}
    # data = version_manager.update_version(version_id=6990, data_to_update=_data)
    version = version_manager.get_version(version_id=7033)
    # data = version_manager.update_version(version_id=6990, data=_data)
    flow.disconnect()
    logger.info(f"data= {version}")

    # data= [
        #     {
        #         'type': 'Version', 'id': 7031, 'code': 'generic_prop_1_002_Modeling_v004', 'client_code': 'v004', 'entity': None, 
        #         # 'created_at': datetime.datetime(2025, 11, 28, 15, 10, 18, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7970e29fee50>), 
        #         'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
        #         'tasks': [], 
        #         'published_files': [{'id': 77, 'name': 'CianLu_V02.v004', 'type': 'PublishedFile'}]
        #     }, 
        #     {
        #         'type': 'Version', 'id': 7030, 'code': '002_Modeling', 'client_code': 'v001', 'entity': None, 
        #         # 'created_at': datetime.datetime(2025, 11, 28, 15, 1, 12, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7970e29fee50>), 
        #         'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
        #         'tasks': [], 
        #         'published_files': [{'id': 76, 'name': 'CianLu_V02.v001', 'type': 'PublishedFile'}]
        #     }, 
        #     {
        #         'type': 'Version', 'id': 7029, 'code': '002_Modeling', 'client_code': 'v001', 'entity': None, 
        #         # 'created_at': datetime.datetime(2025, 11, 28, 15, 0, 47, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7970e29fee50>), 
        #         'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
        #         'tasks': [], 
        #         'published_files': [{'id': 75, 'name': 'CianLu_V02.v001', 'type': 'PublishedFile'}]
        #     }, 
        #     {
        #         'type': 'Version', 'id': 7028, 'code': '002_Modeling', 'client_code': 'v001', 'entity': None, 
        #         # 'created_at': datetime.datetime(2025, 11, 28, 14, 50, 46, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7970e29fee50>), 
        #         'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'tasks': [], 
        #         'published_files': [{'id': 74, 'name': 'CianLu_V02.v001', 'type': 'PublishedFile'}]
        #     }
        # ]
    # data= {
    #         'type': 'Version', 'id': 7031, 'tasks': [], 'sg_task': {'id': 5947, 'name': '002_Modeling', 'type': 'Task'}, 
    #         'published_files': [{'id': 77, 'name': 'CianLu_V02.v004', 'type': 'PublishedFile'}], 
    #         'code': 'generic_prop_1_002_Modeling_v004', 'sg_status_list': 'rev'
    #     }
    # data= {
    #         'type': 'Version', 'id': 7033, 'tasks': [], 'sg_task': {'id': 5947, 'name': '002_Modeling', 'type': 'Task'}, 
    #         'published_files': [
    #                 {'id': 83, 'name': 'CianLu_Body_Color.1001.v006', 'type': 'PublishedFile'}, 
    #                 {'id': 84, 'name': 'CianLu_Body_Color.1002.v006', 'type': 'PublishedFile'}, 
    #                 {'id': 85, 'name': 'CianLu_Body_Color.1003.v006', 'type': 'PublishedFile'}, 
    #                 {'id': 82, 'name': 'CianLu_Body_Color.1005.v006', 'type': 'PublishedFile'}
    #             ], 
    #         'code': 'generic_prop_1__002_Modeling__v006', 'sg_status_list': 'rev'
    #     }