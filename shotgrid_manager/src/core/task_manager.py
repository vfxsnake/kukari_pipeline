from core.base_manager import BaseManager
from typing import List
from utils.logger import setup_logging
import logging


class TaskManager(BaseManager):
    entity = "Task"
    entity_fields = [
        "id", "code", "content", "project", "due_date", "sg_priority_1", "entity", 
        "sg_status_list", "task_assignees", "sg_versions", "step", "name"
    ]

    def get_task(self, task_id:int)->dict:
        return self.get_entity(
            filters=[["id", "is", task_id]],
            fields= self.entity_fields
        )

    def get_tasks_from_user(self, user_id:int)->List[dict]:

        task_list = self.get_entities( 
            filters=[["task_assignees", "is", {"type": "HumanUser", "id":user_id}]], 
            fields= self.entity_fields
        )
        return task_list

    def get_tasks_from_shot(self, shot_id:int)->List[dict]:
        task_list = self.get_entities( 
            filters=[["entity", "is", {"type": "Shot", "id":shot_id}]], 
            fields= self.entity_fields
        )
        return task_list

    def get_tasks_from_asset(self, asset_id:int)->List[dict]:
        task_list = self.get_entities(
            filters=[["entity", "is", {"type": "Asset", "id": asset_id}]],
            fields=self.entity_fields
        )
        return task_list

    def get_tasks_from_project(self, project_id:int):
        task_list = self.get_entities(
            filters=[["project", "is", {"type":"Project", "id":project_id}]],
            fields=self.entity_fields
        )
        return task_list

    def update_status(self, task_id, new_status)->dict:
        data = {"sg_status_list": new_status}
        return self.update_entity(task_id=task_id, new_data=data)
    
    def update_assignee(self, task_id:int, user_id:int)->dict:
        if (task_id < 0 and user_id < 0) or task_id == user_id:
            self.logger.error("invalid data , please provide a valid task and a valid user.")
            return 

        task = self.get_task(task_id=task_id)
        current_assignees = task.get("task_assignees", [])
        if current_assignees:
            for human_user in current_assignees:
                if human_user.get("id", -1) == user_id:
                    logger.info(f"User already assigned, nothing to do.")
                    return task
        current_assignees.append({'type': 'HumanUser', 'id': user_id})
            
        data= {"task_assignees": current_assignees}
        return self.update_entity(entity_id=task_id, data=data)


if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    flow.connect()
    task_manager = TaskManager(shotgun_instance=flow)
    
    tasks = task_manager.get_tasks_from_asset(asset_id=1511)
    # for task in tasks:
    #     updated_task = task_manager.update_assignee(task_id=task.get('id', -1), user_id=121)
    # # logger.info(f"data= {data}")
    logger.info(f"tasks = {tasks}")
    flow.disconnect()


    # task_manager.update_entity(
    #     entity_id=5947,
    #     data={'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'} }
    # )

    # task={
    #     'type': 'Task', 'id': 5947, 'content': '002_Modeling', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 
    #     'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': []
    # }
    # task = {
    #     'type': 'Task', 'id': 6078, 'content': '02_Animacion', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 
    #     'entity': {'id': 1209, 'name': 'sq010_050', 'type': 'Shot'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': []
    # }

    # data= {
    #     'type': 'Task', 
    #     'id': 5947, 
    #     'content': '002_Modeling', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 
    #     'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': [], 'sg_versions': []}

    # data= {
    #     'type': 'Task', 'id': 5947, 'content': '002_Modeling', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': [], 
    #     'sg_versions': [
    #         {'id': 7028, 'name': '002_Modeling', 'type': 'Version'}, 
    #         {'id': 7029, 'name': '002_Modeling', 'type': 'Version'}, 
    #         {'id': 7030, 'name': '002_Modeling', 'type': 'Version'}]
    #     }
    # data = {
    #         'type': 'Task', 'id': 5947, 'content': '002_Modeling', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 
    #         'sg_priority_1': None, 'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [], 
    #         'sg_versions': [
    #             {'id': 7028, 'name': '002_Modeling', 'type': 'Version'}, 
    #             {'id': 7029, 'name': '002_Modeling', 'type': 'Version'}, 
    #             {'id': 7030, 'name': '002_Modeling', 'type': 'Version'}, 
    #             {'id': 7031, 'name': 'generic_prop_1_002_Modeling_v004', 'type': 'Version'}, 
    #             {'id': 7032, 'name': 'generic_prop_1__002_Modeling__v005', 'type': 'Version'}, 
    #             {'id': 7033, 'name': 'generic_prop_1__002_Modeling__v006', 'type': 'Version'}
    #         ]
    #         }
    # tasks = [
    #     {'type': 'Task', 'id': 5968, 'content': '001_Art', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 13, 'name': 'Art', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5969, 'content': '002_Modeling', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 14, 'name': 'Model', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5970, 'content': '003_Rigg', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 15, 'name': 'Rig', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5971, 'content': '004_Textures', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 16, 'name': 'Texture', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5972, 'content': '005_Surfacing', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 142, 'name': 'Surfacing', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5973, 'content': '007_Fx', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 137, 'name': 'Character FX', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5974, 'content': '010_Output', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 182, 'name': 'Delivery', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5975, 'content': '008_Render', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 180, 'name': 'Render', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5976, 'content': '006_Lighting', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 176, 'name': 'LightRig', 'type': 'Step'}}, 
    #     {'type': 'Task', 'id': 5977, 'content': '009_Comp', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1511, 'name': '01_Cianlu', 'type': 'Asset'}, 'sg_status_list': 'wtg', 'task_assignees': [{'id': 19, 'name': 'Artist 1', 'type': 'HumanUser'}, {'id': 121, 'name': 'dev pipeline', 'type': 'HumanUser'}], 'sg_versions': [], 'step': {'id': 181, 'name': 'Comp', 'type': 'Step'}}
    # ]