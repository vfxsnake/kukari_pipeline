from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging


class TaskManager(BaseManager):
    entity = "Task"

    def get_tasks(self, user_id:int):
        self.connect()
        task_list = self.manager.instance.find(
            entity_type=self.entity, 
            filters=[["task_assignees", "is", {"type": "HumanUser", "id":user_id}]], 
            fields=["id", "code", "content", "project", "due_date", "sg_priority_1", "entity", "sg_status_list"]
        )
        self.close()
        return task_list

    def update_task(self, task_id, new_data):
        self.connect()
        updated_task = self.manager.instance.update(entity_type=self.entity, entity_id=task_id, data=new_data)
        self.close()
        return updated_task

    def update_status(self, task_id, new_status):
        data = {'sg_status_list': new_status}
        return self.update_task(task_id=task_id, new_data=data)
    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    task_manager = TaskManager(shotgun_instance=flow)
    task_manager.connect()
    data = task_manager.get_tasks(19)
    logger.info(f"data: {data}")
    task_manager.close()
