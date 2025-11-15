import logging

import shotgun_api3 as sg
from core.shotgrid_instance import ShotgridInstance
from utils.logger import setup_logging

class BaseManager():
    logger = logging.getLogger(__name__)
    entity = ""
    
    def __init__(self, shotgun_instance:ShotgridInstance):
        self.manager = shotgun_instance
        setup_logging()

    def close(self):
        if self.manager:
            self.manager.close_connection()
    
    def connect(self):
        self.manager.open_connection()
