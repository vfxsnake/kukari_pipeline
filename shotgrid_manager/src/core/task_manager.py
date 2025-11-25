from core.base_manager import BaseManager
from typing import List
from utils.logger import setup_logging
import logging


class TaskManager(BaseManager):
    entity = "Task"
    entity_fields = ["id", "code", "content", "project", "due_date", "sg_priority_1", "entity", "sg_status_list"]

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
        data = {'sg_status_list': new_status}
        return self.update_entity(task_id=task_id, new_data=data)


if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    task_manager = TaskManager(shotgun_instance=flow)
    data = task_manager.get_tasks_from_project(project_id=124)
    logger.info(f"data: {data}")
    task_manager.close()
