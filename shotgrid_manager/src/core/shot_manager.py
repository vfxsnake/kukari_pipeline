from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging



class ShotManager(BaseManager):
    entity = "Shot"
    entity_fields = []

    def create_shot(self, project_id:int, name:str, task_template:dict=None)->dict:
        """
        Args:
            project_id: project shotgun id
            name: the name of the Shot. Very important, should be unique as it will be used to construct the
                  path in the storage.
            task_template: the shotgun task template entity dictionary {'type': 'TaskTemplate', 'id': 00}
        """
        shot_data = {
            "project": {"type": "Project", "id": project_id},
            "code": name,
        }
        if task_template:
            shot_data.setdefault("task_template", task_template)
        
        created_shot =  self.create_entity(data = shot_data)
        return created_shot
    

if __name__ == "__main__":

    # SandBox project:
    # {'id': 124, 'name': 'SandBox', 'type': 'Project'}

    # Kukari Task templates
    # [ 
    #     {'type': 'TaskTemplate', 'id': 46, 'code': 'Kukari_Animation_Assets'}, 
    #     {'type': 'TaskTemplate', 'id': 47, 'code': 'Kukari_Animation_Shots'}
    # ]

    # shot = {
    #     'id': 1174, 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'code': 'generic_shot_00', 
    #     'task_template': {'id': 47, 'name': 'Kukari_Animation_Shots', 'type': 'TaskTemplate'}, 
    #     'type': 'Shot'
    # }


    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    asset_manager = ShotManager(shotgun_instance=flow)
    
    

    print(created_shot)



