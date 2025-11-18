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
    import requests
    import shutil

    setup_logging()
    logger = logging.getLogger(__name__)
    
    flow = ShotgridInstance()
    flow.open_connection()
    # schemas = flow.instance.schema_field_read(entity_type="Attachment")
    # entities = flow.instance.find(entity_type="Attachment", filters=[["project", "is", {"type": "Project", "id":124}]], fields=["id", "code", "content", "project", "due_date", "sg_priority_1"])
    # for element in entities:
    #     task_assignees = element.get("task_assignees", [])
    #     task_assignees.append({'type': 'HumanUser', 'id': 19, 'name': 'Artist 1'})
    #     data = {"task_assignees": task_assignees}
    #     flow.instance.update(entity_type=element.get('type', "Task"), entity_id=element.get('id', 19), data=data)
    # fields = [
    # 'code','description','name','filmstrip_image','path_cache','path_cache_storage','version','task','path','version_number','cached_display_name','updated_by','created_by',
    # 'published_file_type', 'sg_status_list', 'updated_at', 'created_at', 'project', 'id', 'tags', 'upstream_published_files', 'downstream_published_files', 'image',
    # 'image_source_entity', 'entity', 'image_blur_hash'
    # ]

    fields = ['cached_display_name', 'original_fname', 'id',
    'attachment_links', 'this_file', 'updated_at',
    'file_extension', 'description', 'filename', 'display_name', 'created_at']

    entities = flow.instance.find(entity_type="Attachment", filters=[["id", "is", 673]], fields=fields)

    # url = flow.instance.download_attachment( 673, file_path="/mnt/c/Users/jazzj/Documents/Projects/shot_grid_test/CianLu_downloaded_v003.abc")

    # response = requests.get(url, stream=True)
    # response.raise_for_status() # Raise an exception for bad status codes

    # # Save the file in chunks to avoid loading the entire file into memory
    # local_file = "/mnt/c/Users/jazzj/Documents/Projects/shot_grid_test/CianLu_downloaded_v002.abc"
    # with open(local_file, 'wb') as f:
    #     shutil.copyfileobj(response.raw, f)

    logger.info(f"Attachment : {entities}")
    flow.close_connection()

