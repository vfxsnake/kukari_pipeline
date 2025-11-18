from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging


class AssetManager(BaseManager):
    entity = "Asset"

    def create_asset(self, project_id:int, name:str, task_template:dict)->dict:
        asset_data = {
            "project": {"type": "Project", "id": project_id},
            "code": name,
        }
        if task_template:
            asset_data.setdefault("task_template", task_template)

        created_asset =  self.create_entity(data = asset_data)

        return created_asset
    
    def create_character(self, project_id:int, name:str, template_id:int)->dict:
        task_template = {'type': 'TaskTemplate', 'id': template_id}
        return self.create_asset(project_id=project_id, name=name, task_template=task_template)
    
    def create_environment(self)->dict:
        pass

    def create_prop(self)->dict:
        pass


if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    asset_manager = AssetManager(shotgun_instance=flow)
    
    