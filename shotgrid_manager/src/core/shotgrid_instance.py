'''
    Opens the connection to shotgun
    and returns the shotgun Object ready to start working with

'''
import os
import shotgun_api3 as sg
import logging
from utils.logger import setup_logging

class ShotgridInstance(): 
    
    logger = logging.getLogger(__name__)

    def __init__(self):
        
        setup_logging()
        self.instance = None

    def open_connection(self):
        if self.instance:
            self.instance.connect()
            return True

        url = os.getenv('SG_URL')
        script_name = os.getenv('SG_SCRIPT_NAME')
        api_key = os.getenv('SG_SCRIPT_KEY')

        if not (url and script_name and api_key):
            self.logger.error("invalid keys, please check you environment variables")
            raise ConnectionAbortedError("no valid keys for log in")
        
        _sg = None
        try: 
            _sg = sg.shotgun.Shotgun(
                base_url=os.getenv('SG_URL'),
                script_name=os.getenv('SG_SCRIPT_NAME'),
                api_key=os.getenv('SG_SCRIPT_KEY')
            )
        except:
            raise ConnectionError(f"unable to connect to {os.getenv('SG_URL')}")

        if _sg:
            self.instance = _sg
            self.logger.info("connection success")
            return True
        
        return False

    
    def close_connection(self):
        if self.instance:
            self.instance.close()


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    
    flow = ShotgridInstance()
    flow.open_connection()

    entities = flow.instance.find(entity_type="Task", filters=[["task_assignees", "is", {"type": "HumanUser", "id":19}]], fields=["id", "code", "content", "project", "due_date", "sg_priority_1"])
    # for element in entities:
    #     task_assignees = element.get("task_assignees", [])
    #     task_assignees.append({'type': 'HumanUser', 'id': 19, 'name': 'Artist 1'})
    #     data = {"task_assignees": task_assignees}
    #     flow.instance.update(entity_type=element.get('type', "Task"), entity_id=element.get('id', 19), data=data)

    # entities = flow.instance.find(entity_type="Task", filters=[["project", "is", {"type": "Project", "id":124}]], fields=["id", "code", "content", "project", "task_assignees"])

    logger.info(f"Tasks : {entities}")
    flow.close_connection()

