from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging


class AssetManager(BaseManager):
    entity = "Asset"

    def create_asset(self, project_id:int, name:str, task_template:dict=None)->dict:
        asset_data = {
            "project": {"type": "Project", "id": project_id},
            "code": name,
        }
        if task_template:
            asset_data.setdefault("task_template", task_template)
        self.connect()
        created_asset =  self.manager.instance.create(self.entity, data = asset_data)
        self.close()
        return created_asset
    
    def create_character(self, project_id:int, name:str, template_id:int):
        task_template = {'type': 'TaskTemplate', 'id': template_id}
        return self.create_asset(project_id=project_id, name=name, task_template=task_template)
    
    def create_environment(self):
        pass

    def create_prop(self):
        pass


if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    asset_manager = AssetManager(shotgun_instance=flow)
    
    