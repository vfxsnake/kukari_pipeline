# -*- coding: utf-8 -*-
"""
ShotGrid Task Data Model

Client-side caching layer for task data.
Provides fast filtering, searching, and sorting without ShotGrid API calls.
"""

from typing import List, Set, Optional, Dict
from datetime import datetime
import logging


class ShotgridTaskDataModel:
    """
    Data model for caching and querying ShotGrid tasks.

    Implements client-side caching for better performance:
    - Fetch data once from ShotGrid
    - Filter/search/sort locally (instant)
    - Refresh only when needed (manual, status change, publish)

    Usage:
        # Load data once
        tasks = task_manager.get_entities(...)
        model = ShotgridTaskDataModel(tasks)

        # Fast local queries
        filtered = model.filter_tasks(project_id=123, entity_name="char_hero")
        searched = model.search_tasks("animation")

        # Optimistic updates
        model.update_task_status(task_id, "ip")

        # Refresh from server
        fresh_data = task_manager.get_entities(...)
        model.refresh(fresh_data)
    """

    def __init__(self, task_data: List[dict]):
        """
        Initialize model with task data.

        Args:
            task_data: List of task dictionaries from ShotGrid
        """
        self._data = task_data
        self._last_updated = datetime.now()
        self._logger = logging.getLogger(__name__)

        self._logger.info(f"Initialized model with {len(task_data)} tasks")

    @property
    def last_updated(self) -> datetime:
        """Get timestamp of last data refresh"""
        return self._last_updated

    @property
    def task_count(self) -> int:
        """Get total number of tasks in cache"""
        return len(self._data)

    def get_all_tasks(self) -> List[dict]:
        """Get all cached tasks"""
        return self._data.copy()

    def get_task_by_id(self, task_id: int) -> Optional[dict]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to find

        Returns:
            Task dictionary or None if not found
        """
        for task in self._data:
            if task.get('id') == task_id:
                return task
        return None

    def get_projects(self) -> Set[tuple]:
        """
        Get unique projects from cached tasks.

        Returns:
            Set of (project_name, project_id) tuples
        """
        projects = set()
        for task in self._data:
            project = task.get('project', {})
            if project:
                name = project.get('name')
                proj_id = project.get('id')
                if name and proj_id:
                    projects.add((name, proj_id))
        return projects

    def get_entities(self) -> Set[tuple]:
        """
        Get unique entities (assets/shots) from cached tasks.

        Returns:
            Set of (entity_name, entity_type) tuples
        """
        entities = set()
        for task in self._data:
            entity = task.get('entity', {})
            if entity:
                # Try 'code' first (for Assets), fall back to 'name' (for Shots)
                entity_name = entity.get('code') or entity.get('name')
                entity_type = entity.get('type')
                if entity_name and entity_type:
                    entities.add((entity_name, entity_type))
        return entities

    def filter_tasks(
        self,
        project_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_name: Optional[str] = None,
        task_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[dict]:
        """
        Filter tasks by various criteria.

        Args:
            project_id: Filter by project ID
            entity_type: Filter by entity type ("Shot" or "Asset")
            entity_name: Filter by entity name/code (e.g., "char_hero", "shot_010")
            task_name: Filter by task type/step
            status: Filter by status code

        Returns:
            Filtered list of tasks
        """
        filtered = self._data

        # Project filter
        if project_id is not None:
            filtered = [
                t for t in filtered
                if t.get('project', {}).get('id') == project_id
            ]

        # Entity type filter
        if entity_type:
            filtered = [
                t for t in filtered
                if t.get('entity', {}).get('type') == entity_type
            ]

        # Entity name filter (matches both 'code' and 'name' fields)
        if entity_name:
            entity_name_lower = entity_name.lower()
            filtered = [
                t for t in filtered
                if entity_name_lower in (t.get('entity', {}).get('code', '').lower() or
                                        t.get('entity', {}).get('name', '').lower())
            ]

        # Task name filter (matches content field)
        if task_name:
            filtered = [
                t for t in filtered
                if t.get('content', "") == task_name
            ]

        # Status filter
        if status:
            filtered = [
                t for t in filtered
                if t.get('sg_status_list') == status
            ]

        return filtered

    def search_tasks(self, search_text: str) -> List[dict]:
        """
        Search tasks by content/name and entity name.

        Args:
            search_text: Text to search for (case-insensitive)

        Returns:
            Tasks matching search text in task content or entity name
        """
        if not search_text:
            return self._data

        search_lower = search_text.lower()

        results = []
        for task in self._data:
            # Search in task content
            if search_lower in task.get('content', '').lower():
                results.append(task)
                continue

            # Search in entity name/code
            entity = task.get('entity', {})
            entity_name = entity.get('code', '') or entity.get('name', '')
            if search_lower in entity_name.lower():
                results.append(task)

        return results

    def get_tasks_by_status(self, status: str) -> List[dict]:
        """
        Get all tasks with specific status.

        Args:
            status: Status code (e.g., 'wtg', 'ip', 'rev', 'fin')

        Returns:
            Tasks with matching status
        """
        return [
            task for task in self._data
            if task.get('sg_status_list') == status
        ]

    def get_tasks_for_entity(self, entity_name: str, entity_type: Optional[str] = None) -> List[dict]:
        """
        Get all tasks for a specific entity (asset or shot).

        Args:
            entity_name: Entity code/name to filter by
            entity_type: Optional entity type to narrow search ("Asset" or "Shot")

        Returns:
            Tasks for the specified entity
        """
        entity_name_lower = entity_name.lower()

        tasks = []
        for task in self._data:
            entity = task.get('entity', {})

            # Check entity type if specified
            if entity_type and entity.get('type') != entity_type:
                continue

            # Check entity name (code or name)
            ent_name = (entity.get('code', '') or entity.get('name', '')).lower()
            if entity_name_lower == ent_name:
                tasks.append(task)

        return tasks

    def update_task_status(self, task_id: int, new_status: str) -> bool:
        """
        Optimistically update task status in cache.

        This updates the local cache immediately for instant UI feedback.
        The caller should still sync to ShotGrid in the background.

        Args:
            task_id: Task ID to update
            new_status: New status code

        Returns:
            True if task was found and updated, False otherwise
        """
        for task in self._data:
            if task.get('id') == task_id:
                old_status = task.get('sg_status_list')
                task['sg_status_list'] = new_status
                self._logger.debug(
                    f"Optimistically updated task {task_id}: {old_status} -> {new_status}"
                )
                return True

        self._logger.warning(f"Task {task_id} not found in cache for status update")
        return False

    def update_task(self, task_id: int, fields: Dict[str, any]) -> bool:
        """
        Optimistically update task fields in cache.

        Args:
            task_id: Task ID to update
            fields: Dictionary of fields to update

        Returns:
            True if task was found and updated, False otherwise
        """
        for task in self._data:
            if task.get('id') == task_id:
                task.update(fields)
                self._logger.debug(f"Optimistically updated task {task_id}: {fields}")
                return True

        self._logger.warning(f"Task {task_id} not found in cache for update")
        return False

    def refresh(self, new_data: List[dict]):
        """
        Refresh cache with new data from ShotGrid.

        Args:
            new_data: Fresh task data from ShotGrid
        """
        old_count = len(self._data)
        self._data = new_data
        self._last_updated = datetime.now()

        self._logger.info(
            f"Refreshed cache: {old_count} -> {len(new_data)} tasks at {self._last_updated}"
        )

    def add_task(self, task: dict):
        """
        Add new task to cache (e.g., after creating in ShotGrid).

        Args:
            task: Task dictionary to add
        """
        if task.get('id') not in [t.get('id') for t in self._data]:
            self._data.append(task)
            self._logger.debug(f"Added task {task.get('id')} to cache")

    def remove_task(self, task_id: int) -> bool:
        """
        Remove task from cache.

        Args:
            task_id: Task ID to remove

        Returns:
            True if task was found and removed, False otherwise
        """
        for i, task in enumerate(self._data):
            if task.get('id') == task_id:
                self._data.pop(i)
                self._logger.debug(f"Removed task {task_id} from cache")
                return True

        return False

    def get_status_counts(self) -> Dict[str, int]:
        """
        Get count of tasks by status.

        Returns:
            Dictionary mapping status codes to counts
        """
        counts = {}
        for task in self._data:
            status = task.get('sg_status_list', 'unknown')
            counts[status] = counts.get(status, 0) + 1

        return counts
