from core.base_manager import BaseManager
from utils.logger import setup_logging
from typing import List
import logging


class VersionManager(BaseManager):
    entity = "Version"

    def get_versions(self, task_id:int)-> List[dict]:
        """
        returns a list of task dictionaries
        """
        version_list = self.get_entities(
            filters=[["tasks", "is", {"type": "Task", "id":task_id}]], 
            fields=["id", "code", "client_code","entity", "created_at", "project", "tasks", "published_files"],
            order=[{'field_name':'created_at', 'direction':'desc'}]
        )

        return version_list
    
    def create_version(self, task_id:int, name:str, version_code:str, project_id:int)->dict:
        version = self.create_entity(
            data= {
                "project":{"type":"Project", "id":project_id},
                "tasks":[{"type":"Task", "id":task_id}],
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
    
    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    version_manager = VersionManager(shotgun_instance=flow)
    # _data = {}
    # data = version_manager.update_version(version_id=6990, data_to_update=_data)
    version = version_manager.get_versions(task_id=5860)
    # data = version_manager.update_version(version_id=6990, data=_data)

    logger.info(f"data: {version}")
