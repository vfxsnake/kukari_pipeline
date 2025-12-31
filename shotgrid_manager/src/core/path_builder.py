import logging
from typing import List

import shotgun_api3 as sg
from core.shotgrid_instance import ShotgridInstance
from utils.logger import setup_logging

import os

WORK_AREA_PATH = os.getenv("WORK_AREA")

ENTITY_TYPE_MAP = {
    "Asset": "ASSETS",
    "Shot": "SHOTS"
}

ASSETS_TYPE_MAP = {
    "Character": "Characters",
    "Environment": "Environments",
    "Prop": "Props"
}


class PathBuilder():
    """
    Builds file system paths for Shotgun entities.
    Uses composition pattern - receives ShotgridInstance with persistent connection.
    """
    logger = logging.getLogger(__name__)

    def __init__(self, shotgun_instance: ShotgridInstance):
        """
        Initialize PathBuilder with shared Shotgun instance.

        Args:
            shotgun_instance: ShotgridInstance with active connection
        """
        self.manager = shotgun_instance
        setup_logging()

    def _ensure_connected(self):
        """Verify connection is active before operations."""
        self.manager.ensure_connected()

    def get_path_from_task(self, task_id: int) -> str:
        """
        Build file system path from task ID.

        Args:
            task_id: Shotgun task ID

        Returns:
            Full path string, or empty string if unable to build path

        Example:
            /WORK_AREA/ProjectName/ASSETS/Characters/CharName/TaskName
        """
        self._ensure_connected()

        task = self.manager.instance.find_one(
            entity_type="Task",
            filters=[["id", "is", task_id]],
            fields=[
                'content', 'sg_versions', 'project', 'id',
                'entity', 'entity.Asset.sg_asset_type', 'entity.Asset.code'
            ]
        )

        if not task:
            self.logger.error(f"Unable to find task with id {task_id}")
            return ""

        # Extract path components
        task_name = task.get("content", "")
        project = task.get("project", {}).get("name", "")
        entity_type = task.get("entity", {}).get("type", "")

        entity_name = ""
        if entity_type == "Asset":
            asset_type = task.get("entity.Asset.sg_asset_type", "")
            asset_name = task.get("entity.Asset.code", "")
            if asset_type and asset_name:
                entity_name = f"{ASSETS_TYPE_MAP.get(asset_type)}/{asset_name}"

        elif entity_type == "Shot":
            entity_name = task.get("entity", {}).get("name", "")

        # Build path
        if task_name and project and entity_type and entity_name:
            out_path = f"{WORK_AREA_PATH}/{project}/{ENTITY_TYPE_MAP.get(entity_type)}/{entity_name}/{task_name}"
            self.logger.debug(f"Built path for task {task_id}: {out_path}")
            return out_path

        self.logger.warning(f"Unable to build complete path for task {task_id}")
        return ""

    def get_task_paths_from_asset(self, asset_id: int) -> List[str]:
        """
        Get all task paths for an asset.

        Args:
            asset_id: Shotgun asset ID

        Returns:
            List of path strings for all tasks on the asset
        """
        self._ensure_connected()

        asset = self.manager.instance.find_one(
            entity_type="Asset",
            filters=[["id", "is", asset_id]],
            fields=["tasks"]
        )

        if not asset:
            self.logger.warning(f"Asset {asset_id} not found")
            return []

        paths = []
        for task in asset.get('tasks', []):
            task_path = self.get_path_from_task(task.get("id"))
            if task_path:
                paths.append(task_path)

        self.logger.info(f"Built {len(paths)} paths for asset {asset_id}")
        return paths

    def create_path(self, file_path):
        if file_path:
            os.makedirs(file_path, exist_ok=True)
            self.logger.info(f"path success!!: {file_path}")
        else:
            raise FileExistsError("empty or invalid path provided. {file_path}")
    


if __name__ == "__main__":
    # Test PathBuilder with persistent connection
    sg_instance = ShotgridInstance()

    # Connect once at startup
    sg_instance.connect()

    # Create path builder
    path_builder = PathBuilder(sg_instance)

    # Get path for task - no connection management needed
    task_path = path_builder.get_path_from_task(task_id=6799)
    print(f"Task path: {task_path}")

    # Create directory if path exists
    if task_path:
        path_builder.create_path(task_path)

    # Disconnect once at shutdown
    sg_instance.disconnect()
    

    



