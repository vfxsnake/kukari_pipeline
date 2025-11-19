from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging



class AssetManager(BaseManager):
    entity = "Asset"

    def create_asset(self, project_id:int, name:str, task_template:dict=None, asset_type:str=None)->dict:
        """
        Args:
            project_id: project shotgun id
            name: the name of the asset. Very important, should be unique as it will be used to construct the
                  path in the storage.
            task_template: the shotgun task template entity dictionary {'type': 'TaskTemplate', 'id': 00}
            asset_type: a valid asset type from this list 
                ['Character', 'Environment', 'Prop', 'FX', 'Graphic', 'Matte Painting', 'Vehicle', 'Weapon', 'Model', 'Theme', 'Zone', 'Part']
        """
        asset_data = {
            "project": {"type": "Project", "id": project_id},
            "code": name,
        }
        if task_template:
            asset_data.setdefault("task_template", task_template)
        if asset_type:
            asset_data.setdefault("sg_asset_type", asset_type)
        
        created_asset =  self.create_entity(data = asset_data)

        return created_asset
    
    
    def create_character(self, project_id:int, name:str, template_id:int)->dict:
        """
        Specialized function to create characters, simplifies the number of parameters to 3
        Args:
            project_id: project shotgun id
            name: the name of the asset. Very important, should be unique as it will be used to construct the
                  path in the storage.
            template_id: shotgun id for the task template 
        """
        task_template = {'type': 'TaskTemplate', 'id': template_id}
        return self.create_asset(project_id=project_id, name=name, task_template=task_template, asset_type="Character")
    
    def create_environment(self, project_id:int, name:str, template_id:int)->dict:
        """
        Specialized function to create environments, simplifies the number of parameters to 3
        Args:
            project_id: project shotgun id
            name: the name of the asset. Very important, should be unique as it will be used to construct the
                  path in the storage.
            template_id: shotgun id for the task template 
        """
        task_template = {'type': 'TaskTemplate', 'id': template_id}
        return self.create_asset(project_id=project_id, name=name, task_template=task_template, asset_type="Environment")

    def create_prop(self, project_id:int, name:str, template_id:int)->dict:
        """
        Specialized function to create props, simplifies the number of parameters to 3
        Args:
            project_id: project shotgun id
            name: the name of the asset. Very important, should be unique as it will be used to construct the
                  path in the storage.
            template_id: shotgun id for the task template 
        """
        task_template = {'type': 'TaskTemplate', 'id': template_id}
        return self.create_asset(project_id=project_id, name=name, task_template=task_template, asset_type="Prop")



if __name__ == "__main__":

# SandBox project:
# {'id': 124, 'name': 'SandBox', 'type': 'Project'}

# Kukari Task templates
# [ 
#     {'type': 'TaskTemplate', 'id': 46, 'code': 'Kukari_Animation_Assets'}, 
#     {'type': 'TaskTemplate', 'id': 47, 'code': 'Kukari_Animation_Shots'}
# ]


    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    asset_manager = AssetManager(shotgun_instance=flow)
    
    asset_manager.create_character(project_id=124, name="generic_asset_1", template_id=46)
    asset_manager.create_environment(project_id=124, name="generic_environment_1", template_id=46)
    asset_manager.create_prop(project_id=124, name="generic_prop_1", template_id=46)
