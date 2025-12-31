import logging
from typing import List, Optional, Dict
from core.task_manager import TaskManager
from utils.logger import setup_logging


# ============================================================================
# Pipeline Dependency Configuration
# TODO: Move these to a config file or read from ShotGrid portal
# ============================================================================

# Pipeline dependency rules for assets
# Format: {current_step: [list_of_upstream_steps]}
ASSET_DEPENDENCIES = {
    'Art': [],                      # No upstream dependencies
    'Model': ['Art'],
    'Rig': ['Model'],
    'Surfacing': ['Model'],
    'Texture': ['Model'],
    'Character FX': ['Rig'],
    'LightRig': ['Surfacing'],
    'Render': ['LightRig'],
    'Delivery': ['Render'],
}

# Pipeline dependency rules for shots
# Format: {current_step: [list_of_upstream_steps]}
SHOT_DEPENDENCIES = {
    'Layout': [],                   # No upstream tasks, needs assets
    'Animation': ['Layout'],
    'Lighting': ['Animation'],      # Can fallback to Layout if needed
    'Character FX': ['Animation'],
    'FX': ['Animation'],
    'Render': ['Lighting'],
    'Comp': ['Render'],             # Can fallback to Lighting if needed
}

# Asset step preference for shots (try in order)
SHOT_ASSET_STEP_PREFERENCE = ['Rig', 'Model']

# Version statuses to exclude from queries
EXCLUDED_VERSION_STATUSES = ['rej', 'omt']  # rejected, omitted


class DependencyResolver:
    """
    Resolves task dependencies based on pipeline rules.

    For asset tasks, finds upstream tasks from the same asset.
    For shot tasks, finds upstream tasks and linked asset dependencies.

    Usage:
        resolver = DependencyResolver(task_manager)
        dependencies = resolver.get_dependencies(task_id=123)
    """

    def __init__(self, task_manager: TaskManager):
        """
        Initialize DependencyResolver.

        Args:
            task_manager: TaskManager instance with active ShotGrid connection
        """
        self.task_manager = task_manager
        self.shotgrid_instance = task_manager.manager  # Access to ShotgridInstance
        self.logger = logging.getLogger(__name__)
        setup_logging()

        # Current task being processed (set by get_dependencies)
        self.task = None

        # Lazy-loaded managers
        self._version_manager = None
        self._asset_manager = None
        self._shot_manager = None

    # ========================================================================
    # Public API
    # ========================================================================

    def get_dependencies(self, task_id: int) -> List[Dict]:
        """
        Get all dependencies for a task by ID.

        Args:
            task_id: ShotGrid task ID

        Returns:
            List of dependency dictionaries, each containing:
                - source: 'upstream_task' or 'asset_dependency'
                - task: Task entity dict
                - entity: Asset/Shot entity dict
                - step: Step entity dict
                - version: Latest version dict (or None)
                - published_files: List of published file dicts
                - version_warning: Warning message if no version (or None)
                - preferred_step: (asset deps only) What step we wanted
                - actual_step: (asset deps only) What step we got
                - is_fallback: (asset deps only) True if using fallback

        Raises:
            ValueError: If task not found
        """
        # Fetch and store task
        self.task = self.task_manager.get_task(task_id)

        if not self.task:
            raise ValueError(f"Task with id {task_id} not found")

        self.logger.info(
            f"Resolving dependencies for task {task_id} "
            f"({self._get_step_name()} on {self._get_entity_type()})"
        )

        dependencies = []

        # Get upstream task dependencies
        upstream_deps = self._get_upstream_dependencies()
        dependencies.extend(upstream_deps)

        # Get asset dependencies (if shot task)
        if self._is_shot_task():
            asset_deps = self._get_asset_dependencies()
            dependencies.extend(asset_deps)

        self.logger.info(f"Found {len(dependencies)} total dependencies")
        return dependencies

    # ========================================================================
    # Task Property Accessors (using self.task)
    # ========================================================================

    def _get_step_name(self) -> str:
        """Extract step name from current task."""
        step_name = self.task.get('step', {}).get('name', '')

        if not step_name:
            self.logger.warning(
                f"Task {self.task.get('id')} has no step name"
            )

        return step_name

    def _get_entity_type(self) -> str:
        """Get entity type from current task (Asset or Shot)."""
        entity_type = self.task.get('entity', {}).get('type', '')

        if not entity_type:
            self.logger.warning(
                f"Task {self.task.get('id')} has no entity type"
            )

        return entity_type

    def _get_entity_id(self) -> int:
        """Get entity ID from current task."""
        entity_id = self.task.get('entity', {}).get('id', -1)

        if entity_id == -1:
            self.logger.error(
                f"Task {self.task.get('id')} has no valid entity ID"
            )

        return entity_id

    def _get_project(self) -> Dict:
        """Get project dict from current task."""
        project = self.task.get('project', {})

        if not project:
            self.logger.warning(
                f"Task {self.task.get('id')} has no project"
            )

        return project

    def _is_shot_task(self) -> bool:
        """Check if current task belongs to a Shot."""
        return self._get_entity_type() == 'Shot'

    def _is_asset_task(self) -> bool:
        """Check if current task belongs to an Asset."""
        return self._get_entity_type() == 'Asset'

    # ========================================================================
    # Pipeline Rules
    # ========================================================================

    def _get_upstream_step_names(self, step_name: str, entity_type: str) -> List[str]:
        """
        Get upstream step names based on pipeline rules.

        Args:
            step_name: Current step name (e.g., 'Modeling')
            entity_type: Entity type ('Asset' or 'Shot')

        Returns:
            List of upstream step names
        """
        if entity_type == 'Asset':
            return ASSET_DEPENDENCIES.get(step_name, [])
        elif entity_type == 'Shot':
            return SHOT_DEPENDENCIES.get(step_name, [])
        else:
            self.logger.warning(
                f"Unknown entity type '{entity_type}' for step '{step_name}'"
            )
            return []

    # ========================================================================
    # Manager Lazy-Loading
    # ========================================================================

    def _get_version_manager(self):
        """Lazy-load VersionManager."""
        if not self._version_manager:
            from core.version_manger import VersionManager
            self._version_manager = VersionManager(self.shotgrid_instance)
            self.logger.debug("Initialized VersionManager")
        return self._version_manager

    def _get_asset_manager(self):
        """Lazy-load AssetManager."""
        if not self._asset_manager:
            from core.asset_manager import AssetManager
            self._asset_manager = AssetManager(self.shotgrid_instance)
            self.logger.debug("Initialized AssetManager")
        return self._asset_manager

    def _get_shot_manager(self):
        """Lazy-load ShotManager."""
        if not self._shot_manager:
            from core.shot_manager import ShotManager
            self._shot_manager = ShotManager(self.shotgrid_instance)
            self.logger.debug("Initialized ShotManager")
        return self._shot_manager

    # ========================================================================
    # Version Queries
    # ========================================================================

    def _get_latest_version(self, task_id: int) -> Optional[Dict]:
        """
        Get latest non-rejected version for a task.

        Args:
            task_id: Task ID to get version for

        Returns:
            Version dict with published_files, or None if no valid version
        """
        version_mgr = self._get_version_manager()

        # Query versions, excluding rejected/omitted
        versions = version_mgr.get_entities(
            filters=[
                ['sg_task', 'is', {'type': 'Task', 'id': task_id}],
                ['sg_status_list', 'not_in', EXCLUDED_VERSION_STATUSES]
            ],
            fields=[
                'id', 'code', 'created_at', 'published_files',
                'sg_status_list', 'sg_task'
            ],
            order=[{'field_name': 'created_at', 'direction': 'desc'}]
        )

        if versions:
            latest = versions[0]  # First result is latest
            self.logger.debug(
                f"Found version {latest.get('id')} for task {task_id}"
            )
            return latest
        else:
            self.logger.debug(f"No valid version found for task {task_id}")
            return None

    # ========================================================================
    # Upstream Dependencies
    # ========================================================================

    def _get_upstream_dependencies(self) -> List[Dict]:
        """
        Get upstream task dependencies for current task.

        Returns:
            List of dependency dicts with task, version, files info
        """
        step_name = self._get_step_name()
        entity_type = self._get_entity_type()

        # Get upstream step names from pipeline rules
        upstream_steps = self._get_upstream_step_names(step_name, entity_type)

        if not upstream_steps:
            self.logger.debug(
                f"No upstream dependencies for {step_name} on {entity_type}"
            )
            return []

        self.logger.debug(
            f"Looking for upstream tasks with steps: {upstream_steps}"
        )

        # Query upstream tasks from same entity
        upstream_tasks = self.task_manager.get_entities(
            filters=[
                ['entity', 'is', self.task.get('entity')],
                ['step.Step.code', 'in', upstream_steps],
                ['project', 'is', self._get_project()]
            ],
            fields=['id', 'content', 'entity', 'step', 'project']
        )

        self.logger.info(f"Found {len(upstream_tasks)} upstream tasks")

        # Build dependency list
        dependencies = []
        for upstream_task in upstream_tasks:
            dep = self._build_dependency_dict(
                source='upstream_task',
                task=upstream_task
            )
            dependencies.append(dep)

        return dependencies

    # ========================================================================
    # Asset Dependencies (for Shot tasks)
    # ========================================================================

    def _get_asset_dependencies(self) -> List[Dict]:
        """
        Get asset dependencies for shot task.

        Returns:
            List of asset dependency dicts
        """
        if not self._is_shot_task():
            return []

        shot_id = self._get_entity_id()
        shot_mgr = self._get_shot_manager()

        # Get shot with linked assets
        shot = shot_mgr.get_entity(
            filters=[['id', 'is', shot_id]],
            fields=['id', 'code', 'assets']
        )

        if not shot:
            self.logger.error(f"Could not retrieve shot {shot_id}")
            return []

        linked_assets = shot.get('assets', [])

        if not linked_assets:
            self.logger.info(f"Shot {shot_id} has no linked assets")
            return []

        self.logger.info(
            f"Shot {shot_id} has {len(linked_assets)} linked assets"
        )

        # Get task for each asset with step preference
        dependencies = []

        for asset in linked_assets:
            asset_name = asset.get('name', 'Unknown')

            asset_task = self._resolve_asset_task_with_fallback(
                asset=asset,
                preferred_steps=SHOT_ASSET_STEP_PREFERENCE
            )

            if asset_task:
                actual_step = asset_task.get('step', {}).get('name', '')
                preferred_step = SHOT_ASSET_STEP_PREFERENCE[0]

                dep = self._build_dependency_dict(
                    source='asset_dependency',
                    task=asset_task,
                    preferred_step=preferred_step,
                    actual_step=actual_step
                )
                dependencies.append(dep)
            else:
                self.logger.warning(
                    f"No task found for asset {asset_name} "
                    f"with steps {SHOT_ASSET_STEP_PREFERENCE}"
                )

        return dependencies

    def _resolve_asset_task_with_fallback(
        self,
        asset: Dict,
        preferred_steps: List[str]
    ) -> Optional[Dict]:
        """
        Get asset task, trying preferred steps in order.

        Args:
            asset: Asset entity dict {'type': 'Asset', 'id': 123, 'name': 'Cianlu'}
            preferred_steps: List of step names to try ['Rig', 'Model']

        Returns:
            Task dict or None if no task found for any step
        """
        asset_name = asset.get('name', f"Asset {asset.get('id')}")

        for step_name in preferred_steps:
            task = self.task_manager.get_entity(
                filters=[
                    ['entity', 'is', asset],
                    ['step.Step.code', 'is', step_name],
                    ['project', 'is', self._get_project()]
                ],
                fields=['id', 'content', 'entity', 'step', 'project']
            )

            if task:
                self.logger.debug(
                    f"Found {step_name} task for asset {asset_name}"
                )
                return task

        # No task found for any preferred step
        self.logger.warning(
            f"No task found for asset {asset_name} "
            f"with steps {preferred_steps}"
        )
        return None

    # ========================================================================
    # Building Dependency Results
    # ========================================================================

    def _build_dependency_dict(
        self,
        source: str,
        task: Dict,
        preferred_step: Optional[str] = None,
        actual_step: Optional[str] = None
    ) -> Dict:
        """
        Build dependency dictionary with version and file info.

        Args:
            source: 'upstream_task' or 'asset_dependency'
            task: Task entity dict
            preferred_step: What step we wanted (for fallback tracking)
            actual_step: What step we got

        Returns:
            Complete dependency dictionary
        """
        # Get latest valid version
        version = self._get_latest_version(task.get('id', -1))

        # Build base dependency object
        dependency = {
            'source': source,
            'task': task,
            'entity': task.get('entity', {}),
            'step': task.get('step', {}),
            'version': version,
            'version_warning': None,
            'published_files': [],
        }

        # Add version data or warning
        if version:
            dependency['published_files'] = version.get('published_files', [])
            self.logger.debug(
                f"Version {version.get('id')} has "
                f"{len(dependency['published_files'])} published files"
            )
        else:
            step_name = task.get('step', {}).get('name', 'Unknown')
            entity_name = task.get('entity', {}).get('name', 'Unknown')
            dependency['version_warning'] = (
                f"No approved version available for {step_name} on {entity_name}"
            )

        # Track fallback for asset dependencies
        if source == 'asset_dependency' and preferred_step and actual_step:
            dependency['preferred_step'] = preferred_step
            dependency['actual_step'] = actual_step
            dependency['is_fallback'] = (preferred_step != actual_step)

            if dependency['is_fallback']:
                entity_name = task.get('entity', {}).get('name', 'Unknown')
                dependency['version_warning'] = (
                    f"Using {actual_step} for {entity_name} "
                    f"(no {preferred_step} available)"
                )

        return dependency


if __name__ == "__main__":
    """Test DependencyResolver with real ShotGrid data."""
    from core.shotgrid_instance import ShotgridInstance

    setup_logging()
    logger = logging.getLogger(__name__)

    # Connect to ShotGrid
    sg_instance = ShotgridInstance()
    sg_instance.connect()

    # Create managers
    task_mgr = TaskManager(sg_instance)
    resolver = DependencyResolver(task_mgr)

    # Test with a modeling task on an asset
    # Task ID 5947: '002_Modeling' on asset 'generic_prop_1'
    try:
        logger.info("=" * 60)
        logger.info("Testing with Asset Modeling task (ID: 5947)")
        logger.info("=" * 60)

        dependencies = resolver.get_dependencies(task_id=5947)

        logger.info(f"\nFound {len(dependencies)} dependencies:")
        for dep in dependencies:
            logger.info(f"\n  Source: {dep['source']}")
            logger.info(f"  Task: {dep['task'].get('content')} (ID: {dep['task'].get('id')})")
            logger.info(f"  Entity: {dep['entity'].get('name')} ({dep['entity'].get('type')})")
            logger.info(f"  Step: {dep['step'].get('name')}")
            logger.info(f"  Version: {dep['version'].get('id') if dep['version'] else 'None'}")
            logger.info(f"  Published Files: {len(dep['published_files'])}")
            if dep.get('version_warning'):
                logger.info(f"  Warning: {dep['version_warning']}")

    except Exception as e:
        logger.error(f"Error testing asset task: {e}", exc_info=True)

    # Test with a shot animation task
    # Task ID 6078: '02_Animacion' on shot 'sq010_050'
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Testing with Shot Animation task (ID: 6078)")
        logger.info("=" * 60)

        dependencies = resolver.get_dependencies(task_id=6078)

        logger.info(f"\nFound {len(dependencies)} dependencies:")
        for dep in dependencies:
            logger.info(f"\n  Source: {dep['source']}")
            logger.info(f"  Task: {dep['task'].get('content')} (ID: {dep['task'].get('id')})")
            logger.info(f"  Entity: {dep['entity'].get('name')} ({dep['entity'].get('type')})")
            logger.info(f"  Step: {dep['step'].get('name')}")
            logger.info(f"  Version: {dep['version'].get('id') if dep['version'] else 'None'}")
            logger.info(f"  Published Files: {len(dep['published_files'])}")
            if dep.get('version_warning'):
                logger.info(f"  Warning: {dep['version_warning']}")
            if dep.get('is_fallback'):
                logger.info(f"  Fallback: {dep['preferred_step']} → {dep['actual_step']}")

    except Exception as e:
        logger.error(f"Error testing shot task: {e}", exc_info=True)

    # Disconnect
    sg_instance.disconnect()
    logger.info("\n" + "=" * 60)
    logger.info("Tests complete")
    logger.info("=" * 60)
