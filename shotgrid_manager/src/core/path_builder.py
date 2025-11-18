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
    logger = logging.getLogger(__name__)

    
    def __init__(self, shotgun_instance:ShotgridInstance):
        self.manager = shotgun_instance
        setup_logging()

    def get_path_from_task(self, task_id):
        self.manager.open_connection()
        task = self.manager.instance.find_one(
            entity_type="Task",
            filters=[["id", "is", task_id]],
            fields= [
                'code','sg_versions', 'created_at', 'project', 'id',
                'entity', 'entity.sg_asset_type', 'entity.sg_shot_type' 
            ]
        )
        self.manager.close_connection()
        if task:
            self.logger.info(f"task: {task}")
            task_name = task.get("code", "")
            project = task.get("Project", {}).get("name", "")
            entity_type = task.get("entity", {}).get("type", "")
            entity_name = ""
            if entity_type == "Asset":
                asset_type = task.get("entity", {}).get("sg_asset_type", "")
                asset_name = task.get("entity", {}).get("code", "")
                if asset_type and asset_name:
                    entity_name = f"{ASSETS_TYPE_MAP.get(asset_type)}/{asset_name}"
            elif entity_type == "Shot":
                entity_name = task.get("entity", {}).get("code", "")

            if task_name and project and entity_type and entity_name:
                out_path =f"{WORK_AREA_PATH}/{project}/{ENTITY_TYPE_MAP.get(entity_type)}/{entity_name}/{task_name}"
                return out_path
            return ""
    

    def create_path(self, file_path):
        if file_path:
            os.makedirs(file_path, exist_ok=True)
            self.logger.info(f"path success!!: {file_path}")
        else:
            raise FileExistsError("empty or invalid path provided. {file_path}")
    
