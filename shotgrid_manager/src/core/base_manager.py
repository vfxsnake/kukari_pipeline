import logging

from .shotgun_instance import ShotgunInstance
from utils.logger import setup_logging

class BaseManager():
    logger = logging.getLogger(__name__)
    
    def __init__(self, shotgun_instance:ShotgunInstance):
        self.manager = shotgun_instance
        setup_logging()

    def close(self):
        if self.manager:
            self.manager.close_connection()
    
    def connect(self):
        self.manager.open_connection()
