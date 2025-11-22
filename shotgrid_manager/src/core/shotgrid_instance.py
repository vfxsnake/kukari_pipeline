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
    
    # getting schemas
    # schemas = flow.instance.schema_field_read(entity_type="Attachment")
    # print(schemas)
    
    # getting entities
    entities = flow.instance.find(
        entity_type="Asset", 
        filters=[["project", "is", {'id': 124, 'name': 'SandBox', 'type': 'Project'}]], 
        fields= ['code', 'sg_asset_type', "tasks"]
    )
    print(entities)

    # update entities
    # data = {'sg_asset_type': 'Character'}
    # updated_entity = flow.instance.update(entity_type="Asset", entity_id=1445, data=data)
    # print(updated_entity)

    flow.close_connection()



