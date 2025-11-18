import logging
from typing import List

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

    def create_entity(self, data:dict)->dict:
        if not self.entity:
            return
        
        self.connect()
        new_entity = self.manager.instance.create(
            entity_type=self.entity,
            data=data
        )
        self.close()
        return new_entity
    
    def update_entity(self, entity_id:int, data:dict)->dict:
        if not self.entity:
            return {}
        self.connect()
        updated_entity = self.manager.instance.update(
            entity_type=self.entity,
            entity_id=entity_id,
            data=data
        )
        self.close()
        return updated_entity
    
    def get_entities(self, filters:list, fields:List[str], order:List[dict]=None)->List[dict]:
        if not self.entity:
            return []
        self.connect()
        entity_list = self.manager.instance.find(
            entity_type=self.entity,
            filters=filters,
            fields=fields,
            order=order
        )
        self.close()
        return entity_list

    def get_entity(self, filters, fields):
        if not self.entity:
            return {}
        self.connect()
        entity = self.manager.instance.find_one(
            entity_type=self.entity,
            filters=filters,
            fields=fields
        )
        self.close()
        return entity

