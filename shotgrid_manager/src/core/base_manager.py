import logging
from typing import List, Optional

import shotgun_api3 as sg
from core.shotgrid_instance import ShotgridInstance
from utils.logger import setup_logging

class BaseManager():
    """
    Base manager class for Shotgun entity operations.
    Uses composition pattern - receives ShotgridInstance with persistent connection.
    All operations assume connection is already established.
    """
    logger = logging.getLogger(__name__)
    entity = ""
    entity_fields = ["id", "code", "name"]

    def __init__(self, shotgun_instance: ShotgridInstance):
        """
        Initialize manager with shared Shotgun instance.

        Args:
            shotgun_instance: ShotgridInstance with active connection

        Note:
            Connection should already be established before creating managers.
            Call shotgun_instance.connect() at application startup.
        """
        self.manager = shotgun_instance
        setup_logging()

    def _ensure_connected(self):
        """
        Verify connection is active before operations.

        Raises:
            ConnectionError: If not connected to Shotgun
        """
        self.manager.ensure_connected()

    def create_entity(self, data: dict) -> Optional[dict]:
        """
        Create a new entity in Shotgun.

        Args:
            data: Entity data dictionary

        Returns:
            Created entity dictionary, or None if entity type not set
        """
        if not self.entity:
            self.logger.warning("Entity type not set, cannot create entity")
            return None

        self._ensure_connected()

        new_entity = self.manager.instance.create(
            entity_type=self.entity,
            data=data
        )

        self.logger.info(f"Created {self.entity} with id {new_entity.get('id')}")
        return new_entity

    def update_entity(self, entity_id: int, data: dict) -> dict:
        """
        Update an existing entity in Shotgun.

        Args:
            entity_id: Entity ID to update
            data: Fields to update

        Returns:
            Updated entity dictionary
        """
        if not self.entity:
            self.logger.warning("Entity type not set, cannot update entity")
            return {}

        self._ensure_connected()

        updated_entity = self.manager.instance.update(
            entity_type=self.entity,
            entity_id=entity_id,
            data=data
        )

        self.logger.info(f"Updated {self.entity} id {entity_id}")
        return updated_entity

    def get_entities(self, filters: list, fields: List[str], order: List[dict] = None) -> List[dict]:
        """
        Query multiple entities from Shotgun.

        Args:
            filters: Shotgun filter list
            fields: Fields to retrieve
            order: Optional sort order

        Returns:
            List of entity dictionaries
        """
        if not self.entity:
            self.logger.warning("Entity type not set, cannot query entities")
            return []

        self._ensure_connected()

        entity_list = self.manager.instance.find(
            entity_type=self.entity,
            filters=filters,
            fields=fields,
            order=order
        )

        self.logger.debug(f"Found {len(entity_list)} {self.entity} entities")
        return entity_list

    def get_entity(self, filters: list, fields: List[str]) -> Optional[dict]:
        """
        Query single entity from Shotgun.

        Args:
            filters: Shotgun filter list
            fields: Fields to retrieve

        Returns:
            Entity dictionary, or None if not found
        """
        if not self.entity:
            self.logger.warning("Entity type not set, cannot query entity")
            return None

        self._ensure_connected()

        entity = self.manager.instance.find_one(
            entity_type=self.entity,
            filters=filters,
            fields=fields
        )

        if entity:
            self.logger.debug(f"Found {self.entity} id {entity.get('id')}")
        else:
            self.logger.debug(f"No {self.entity} found matching filters")

        return entity

