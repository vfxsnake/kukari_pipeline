from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging



class ShotManager(BaseManager):
    entity = "Shot"
    entity_fields = ["id", "code", "tasks", "assets", "sg_versions", "sg_published_files"]

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
    shot_manager = ShotManager(shotgun_instance=flow)
    flow.connect()

    shots = shot_manager.get_entities(
        filters=[
            ["project", "is", {"type":"Project", "id": 124}], 
            ["code", "is", "sq010_010"]
        ],
        fields=shot_manager.entity_fields
    )

    flow.disconnect()

    print(f"shots = {shots}")

    # shot_list = [
    #     "sq010_010",
    #     "sq010_020",
    #     "sq010_050",
    #     "sq010_060",
    #     "sq010_070",
    #     "sq010_080",
    #     "sq010_090",
    #     "sq010_100",
    #     "sq010_110",
    #     "sq010_120",
    #     "sq010_130",
    #     "sq010_140",
    #     "sq020_010",
    #     "sq020_020",
    #     "sq020_030",
    #     "sq020_040",
    #     "sq020_050",
    #     "sq020_060",
    #     "sq020_070",
    #     "sq020_080",
    #     "sq030_010",
    #     "sq030_020",
    #     "sq030_030",
    #     "sq030_040",
    #     "sq030_050",
    #     "sq030_060",
    #     "sq040_010",
    #     "sq040_020",
    #     "sq040_030",
    #     "sq040_040",
    #     "sq040_050",
    #     "sq040_060",
    #     "sq040_070",
    #     "sq040_080",
    #     "sq050_010",
    #     "sq050_020",
    #     "sq050_030",
    #     "sq050_040",
    #     "sq065_010",
    #     "sq065_020",
    #     "sq070_030",
    #     "sq070_040",
    #     "sq070_050",
    #     "sq070_060",
    #     "sq070_070",
    #     "sq070_080",
    #     "sq070_090",
    #     "sq080_010",
    #     "sq080_020",
    #     "sq080_040",
    #     "sq090_010",
    #     "sq090_020",
    #     "sq090_030",
    #     "sq090_040",
    #     "sq090_050",
    #     "sq090_060",
    #     "sq090_070",
    #     "sq090_080",
    #     "sq090_090",
    #     "sq090_100",
    #     "sq090_110",
    #     "sq090_120",
    #     "sq090_130",
    #     "sq090_140",
    #     "sq090_150",
    #     "sq090_160",
    #     "sq090_170",
    #     "sq090_180",
    #     "sq090_190",
    #     "sq090_200",
    #     "sq090_210",
    #     "sq090_210a",
    #     "sq100_010"
    # ]

    # for shot in shot_list:
    #     shot_manager.create_shot(
    #         project_id=124, 
    #         name=shot, 
    #         task_template={'type': 'TaskTemplate', 'id': 47, 'code': 'Kukari_Animation_Shots'}
    #     )
    #     print(f"{shot} has successfully created")



