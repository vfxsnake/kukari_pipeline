from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging



class AssetManager(BaseManager):
    entity = "Asset"
    entity_fields = ["task_template", "sg_versions", "sg_published_files", "tasks", "sg_status_list", "shots", "assets"]

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

    def get_assets_from_project(self, project_id:int):
        assets = self.get_entities(
            filters=[["project", "is", {"type":"Project", "id": project_id}]],
            fields=self.entity_fields
        )
        return assets
    
    def get_assets_from_shot(self, shot_id):
        assets = self.get_entities(
            filters=["shots", "is", {"type": "Shot", "id": shot_id}],
            fields=self.entity_fields
        )
        return assets

if __name__ == "__main__":
    """
    Test AssetManager with persistent connection pattern.

    SandBox project:
    {'id': 124, 'name': 'SandBox', 'type': 'Project'}

    Kukari Task templates:
    [
        {'type': 'TaskTemplate', 'id': 46, 'code': 'Kukari_Animation_Assets'},
        {'type': 'TaskTemplate', 'id': 47, 'code': 'Kukari_Animation_Shots'}
    ]
    """
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    # Connect once at startup
    sg_instance = ShotgridInstance()
    sg_instance.connect()

    # Create asset manager with shared connection
    asset_manager = AssetManager(shotgun_instance=sg_instance)
    
    # cianlu_01 = asset_manager.create_character(project_id=124, name="01_Cianlu", template_id=46)
    # mascota_bebe_01 = asset_manager.create_character(project_id=124, name="01_MascotaBebe", template_id=46)
    # mascota_adulta_02 = asset_manager.create_character(project_id=124, name="02_MascotaAdulta", template_id=46)

    # int_depa_cianlu_01 = asset_manager.create_environment(project_id=124, name="01_Int_Depa_Cianlu", template_id=46)
    # aldea_principal_03 = asset_manager.create_environment(project_id=124, name="03_AldeaPrincipal", template_id=46)
    # risco_vuelo_04 = asset_manager.create_environment(project_id=124, name="04_riscoVuelo", template_id=46)

    # Example: Create multiple assets using the same connection
    moto_01 = asset_manager.create_prop(project_id=124, name="01_Int_Depa_Cianlu", template_id=46)
    tablet_02 = asset_manager.create_prop(project_id=124, name="03_AldeaPrincipal", template_id=46)
    mochila_voladora_03 = asset_manager.create_prop(project_id=124, name="04_riscoVuelo", template_id=46)

    print(moto_01)
    print(tablet_02)
    print(mochila_voladora_03)

    # asset_manager.create_environment(project_id=124, name="generic_environment_1", template_id=46)
    # asset_manager.create_prop(project_id=124, name="generic_prop_1", template_id=46)

    # Disconnect once at shutdown
    sg_instance.disconnect()


# result = [
#         {'type': 'Asset', 'id': 1445, 'code': 'test_asset_01', 'sg_asset_type': 'Character'}, 
#         {'type': 'Asset', 'id': 1478, 'code': 'generic_asset_1', 'sg_asset_type': 'Character'}, 
#         {'type': 'Asset', 'id': 1479, 'code': 'generic_environment_1', 'sg_asset_type': 'Environment'}, 
#         {'type': 'Asset', 'id': 1480, 'code': 'generic_prop_1', 'sg_asset_type': 'Prop'}
#     ]

# {'id': 1511, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '01_Cianlu', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Character', 'type': 'Asset'}
# {'id': 1512, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '01_MascotaBebe', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Character', 'type': 'Asset'}
# {'id': 1513, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '02_MascotaAdulta', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Character', 'type': 'Asset'}

# {'id': 1514, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '01_Int_Depa_Cianlu', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Environment', 'type': 'Asset'}
# {'id': 1515, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '03_AldeaPrincipal', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Environment', 'type': 'Asset'}
# {'id': 1516, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '04_riscoVuelo', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Environment', 'type': 'Asset'}

# {'id': 1517, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '01_Int_Depa_Cianlu', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Prop', 'type': 'Asset'}
# {'id': 1518, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '03_AldeaPrincipal', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Prop', 'type': 'Asset'}
# {'id': 1519, 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'code': '04_riscoVuelo', 'task_template': {'id': 46, 'name': 'Kukari_Animation_Assets', 'type': 'TaskTemplate'}, 'sg_asset_type': 'Prop', 'type': 'Asset'}