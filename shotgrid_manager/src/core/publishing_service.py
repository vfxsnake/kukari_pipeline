"""
Publishing Service for Shotgrid Manager

Provides flexible publishing workflow for single or multiple files:

High-level workflow:
1. Upload attachment(s) to project
2. Create Version entity
3. Create PublishedFile entity for each attachment
4. Update attachment metadata with links
5. Optionally set task to revision status

Supports:
- Single file publish (work files, scene files)
- Multiple file publish (renders, assets, references)
- Folder publish (as zip via ZipUtility)
"""

from typing import Optional, Dict, Union, List, Callable
import os
import logging
from pathlib import Path

from core.shotgrid_instance import ShotgridInstance
from core.task_manager import TaskManager
from core.version_manger import VersionManager
from core.published_file_manager import PublishedFileManager
from core.attachment_manager import AttachmentManager
from utils.logger import setup_logging
from utils.progress_tracker import ProgressTracker


class PublishingError(Exception):
    """Custom exception for publishing errors"""
    pass


class PublishingService:
    """
    High-level service for publishing files to Shotgrid.

    Orchestrates multiple managers to complete the full publishing workflow.
    Reusable service - task_id is provided at publish time.
    """

    def __init__(self, shotgun_instance: ShotgridInstance):
        """
        Initialize publishing service.

        Args:
            shotgun_instance: Shared ShotgridInstance for all managers
        """
        self.logger = logging.getLogger(__name__)

        # Initialize all required managers with shared connection
        self.task_manager = TaskManager(shotgun_instance=shotgun_instance)
        self.version_manager = VersionManager(shotgun_instance=shotgun_instance)
        self.published_file_manager = PublishedFileManager(shotgun_instance=shotgun_instance)
        self.attachment_manager = AttachmentManager(shotgun_instance=shotgun_instance)

        self.sg_instance = shotgun_instance

        self.logger.info("PublishingService initialized")

    def publish(
        self,
        task_id: int,
        file_path: str,
        description: str = "",
        set_task_to_review: bool = True
    ) -> Dict:
        """
        Execute complete publishing workflow.

        Args:
            task_id: Task ID to publish for
            file_path: Path to file to publish
            description: Optional description for the publish
            set_task_to_review: Whether to set task status to 'rev' (default: True)

        Returns:
            Dictionary with publish results:
            {
                'attachment': attachment_dict,
                'version': version_dict,
                'published_file': published_file_dict,
                'version_number': int,
                'task': updated_task_dict
            }

        Raises:
            PublishingError: If any step of the publishing process fails
            FileNotFoundError: If file_path doesn't exist
        """
        self.logger.info(f"Starting publish workflow for task {task_id}, file: {file_path}")

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Get task data
            self.logger.info("Fetching task data...")
            task_data = self.task_manager.get_task(task_id=task_id)

            if not task_data:
                raise PublishingError(f"Task {task_id} not found")

            # Extract task info
            project_id = task_data.get("project", {}).get("id", -1)
            entity_data = task_data.get('entity', {})
            task_name = task_data.get('content', 'Task')
            entity_name = entity_data.get('name', 'Unknown') if entity_data else 'Unknown'

            self.logger.info(f"Task: {task_name}, Entity: {entity_name}, Project ID: {project_id}")

            # Step 1: Upload attachment to project
            self.logger.info("Step 1/6: Uploading attachment to project...")

            attachment_id = self.upload_attachment(project_id, file_path)
            self.logger.info(f"  ✓ Attachment uploaded (ID: {attachment_id})")

            # Step 2: Determine version number
            self.logger.info("Step 2/6: Determining version number...")
            version_number = self.version_manager.get_next_version_number_for_task(task_id)
            self.logger.info(f"  ✓ Version number: {version_number}")

            # Step 3: Create Version entity
            self.logger.info("Step 3/6: Creating Version entity...")
            version = self.create_version(
                task_id=task_id,
                project_id=project_id,
                version_number=version_number,
                entity_name=entity_name,
                task_name=task_name,
                description=description
            )
            version_id = version.get("id", -1)
            self.logger.info(f"  ✓ Version created (ID: {version_id}, Code: {version.get('code')})")

            # Step 4: Create PublishedFile entity
            self.logger.info("Step 4/6: Creating PublishedFile entity...")
            published_file = self.create_published_file(
                version_id=version_id,
                task_id=task_id,
                project_id=project_id,
                file_path=file_path,
                entity_name=entity_name,
                task_name=task_name,
                version_number=version_number
            )
            published_file_id = published_file['id']
            self.logger.info(f"  ✓ PublishedFile created (ID: {published_file_id}, Code: {published_file.get('code')})")

            # Step 5: Update attachment with metadata
            self.logger.info("Step 5/6: Updating attachment metadata...")
            updated_attachment = self.update_attachment_links(
                attachment_id=attachment_id,
                task_id=task_id,
                version_id=version_id,
                published_file_id=published_file_id,
                file_path=file_path
            )
            self.logger.info(f"  ✓ Attachment metadata updated")

            # Step 6: Set task to revision status
            updated_task = None
            if set_task_to_review:
                self.logger.info("Step 6/6: Setting task to revision status...")
                updated_task = self.set_task_to_review(task_id)
                self.logger.info(f"  ✓ Task status updated to 'rev'")
            else:
                self.logger.info("Step 6/6: Skipping task status update (set_task_to_review=False)")

            # Return complete publish data
            result = {
                'attachment': updated_attachment,
                'version': version,
                'published_file': published_file,
                'version_number': version_number,
                'task': updated_task
            }

            self.logger.info(f"✓ Publishing completed successfully!")
            self.logger.info(f"  - Version: {version.get('code')} (ID: {version_id})")
            self.logger.info(f"  - PublishedFile: {published_file.get('code')} (ID: {published_file_id})")

            return result

        except Exception as e:
            error_msg = f"Publishing failed: {str(e)}"
            self.logger.error(error_msg)
            raise PublishingError(error_msg) from e

    def publish_multiple(
        self,
        task_id: int,
        file_paths: List[str],
        description: str = "",
        set_task_to_review: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict:
        """
        Publish multiple files under one version.

        This is a convenience method that orchestrates the full workflow
        for publishing multiple files (e.g., work file + renders + references)
        all under a single version.

        Args:
            task_id: Task ID to publish for
            file_paths: List of file paths to publish
            description: Optional description for the version
            set_task_to_review: Whether to set task status to 'rev' (default: True)
            progress_callback: Optional callback function(current_step, total_steps, message)
                              Called at each step to report progress

        Returns:
            Dictionary with publish results:
            {
                'version': version_dict,
                'version_number': int,
                'published_files': [pub_file_dict, ...],
                'attachments': [attachment_dict, ...],
                'task': updated_task_dict (if set_task_to_review=True)
            }

        Raises:
            PublishingError: If any step of the publishing process fails
            FileNotFoundError: If any file_path doesn't exist

        Example:
            >>> result = publish_service.publish_multiple(
            ...     task_id=5947,
            ...     file_paths=["scene.ma", "renders.zip", "reference.abc"],
            ...     description="Animation v001",
            ...     progress_callback=lambda cur, tot, msg: print(f"{cur}/{tot}: {msg}")
            ... )
            >>> print(f"Published {len(result['published_files'])} files")
        """
        self.logger.info(f"Starting multi-file publish for task {task_id}")
        self.logger.info(f"Files to publish: {len(file_paths)}")

        # Calculate total steps for progress
        total_steps = len(file_paths) * 2 + 4  # Upload + create pub file for each + 4 steps

        # Create progress tracker
        tracker = ProgressTracker(
            total_steps=total_steps,
            callback=progress_callback,
            logger=self.logger
        )

        # Validate all files exist first
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Get task data
            tracker.step("Fetching task data...")
            task_data = self.task_manager.get_task(task_id=task_id)

            if not task_data:
                raise PublishingError(f"Task {task_id} not found")

            # Extract task info
            project_id = task_data.get("project", {}).get("id", -1)
            entity_data = task_data.get('entity', {})
            task_name = task_data.get('content', 'Task')
            entity_name = entity_data.get('name', 'Unknown') if entity_data else 'Unknown'

            self.logger.info(f"Task: {task_name}, Entity: {entity_name}, Project ID: {project_id}")

            # Step 1: Upload all attachments
            attachment_data = []
            for i, file_path in enumerate(file_paths):
                tracker.step(f"Uploading attachment {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                attachment_id = self.upload_attachment(project_id, file_path)
                attachment_data.append({
                    'id': attachment_id,
                    'file_path': file_path
                })

            # Step 2: Get next version number
            tracker.step("Determining version number...")
            version_number = self.version_manager.get_next_version_number_for_task(task_id)
            self.logger.info(f"Version number: {version_number}")

            # Step 3: Create Version entity (ONE version for all files)
            tracker.step(f"Creating version v{version_number:03d}...")
            version = self.create_version(
                task_id=task_id,
                project_id=project_id,
                version_number=version_number,
                entity_name=entity_name,
                task_name=task_name,
                description=description
            )
            version_id = version['id']
            self.logger.info(f"Version created: {version.get('code')} (ID: {version_id})")

            # Step 4: Create PublishedFile for each attachment
            published_files = []
            for i, att_data in enumerate(attachment_data):
                tracker.step(f"Creating published file {i+1}/{len(attachment_data)}")

                # Create published file
                pub_file = self.create_published_file(
                    version_id=version_id,
                    task_id=task_id,
                    project_id=project_id,
                    file_path=att_data['file_path'],
                    entity_name=entity_name,
                    task_name=task_name,
                    version_number=version_number
                )

                # Update attachment links
                self.update_attachment_links(
                    attachment_id=att_data['id'],
                    task_id=task_id,
                    version_id=version_id,
                    published_file_id=pub_file['id'],
                    file_path=att_data['file_path']
                )

                published_files.append(pub_file)
                self.logger.info(f"PublishedFile created: {pub_file.get('code')} (ID: {pub_file['id']})")

            # Step 5: Set task to review (optional)
            updated_task = None
            if set_task_to_review:
                tracker.step("Setting task to review status...")
                updated_task = self.set_task_to_review(task_id)
                self.logger.info("Task status updated to 'rev'")

            # Return comprehensive result
            result = {
                'version': version,
                'version_number': version_number,
                'published_files': published_files,
                'attachments': attachment_data,
                'task': updated_task
            }

            self.logger.info(f"✓ Multi-file publish completed successfully!")
            self.logger.info(f"  - Version: {version.get('code')} (ID: {version_id})")
            self.logger.info(f"  - Published Files: {len(published_files)}")

            return result

        except Exception as e:
            error_msg = f"Multi-file publishing failed: {str(e)}"
            self.logger.error(error_msg)
            raise PublishingError(error_msg) from e

    # ===================================================================
    # Public Methods - Individual Workflow Steps
    # ===================================================================

    def upload_attachment(self, project_id: int, file_path: str) -> int:
        """
        Upload file attachment to project; 
        shotgun upload function returns only the attachment id
        """
        try:
            attachment_id = self.attachment_manager.upload_attachment_to_project(
                project_id=project_id,
                file_path=file_path
            )

            if not attachment_id > 0:
                raise PublishingError("Upload failed - no attachment ID returned")

            return attachment_id

        except Exception as e:
            raise PublishingError(f"Failed to upload attachment: {str(e)}") from e

    def create_version(
        self,
        task_id: int,
        project_id: int,
        version_number: int,
        entity_name: str,
        task_name: str,
        description: str = ""
    ) -> Dict:
        """
        Create Version entity in ShotGrid.

        Args:
            task_id: Task ID
            project_id: Project ID
            version_number: Version number (e.g., 1, 2, 3)
            entity_name: Entity name (Asset/Shot name)
            task_name: Task name
            description: Optional version description

        Returns:
            Created version dictionary
        """
        # Format version number with padding (v001, v002, etc.)
        version_str = f"v{version_number:03d}"

        # Build names: EntityName_TaskName_v###
        version_name = f"{entity_name}__{task_name}__{version_str}"
        version_code = version_str

        try:
            version = self.version_manager.create_version(
                task_id=task_id,
                name=version_name,
                version_code=version_code,
                project_id=project_id
            )

            # Add description if provided
            if description:
                version = self.version_manager.update_version(
                    version_id=version.get("id", -1),
                    data_to_update={'description': description}
                )

            return version

        except Exception as e:
            raise PublishingError(f"Failed to create version: {str(e)}") from e

    def create_published_file(
        self,
        version_id: int,
        task_id: int,
        project_id: int,
        file_path: str,
        entity_name: str,
        task_name: str,
        version_number: int,
        description:str=""
    ) -> Dict:
        """
        Create PublishedFile entity in ShotGrid.

        Args:
            version_id: Version ID to link to
            task_id: Task ID
            project_id: Project ID
            file_path: Path to file (used for naming)
            entity_name: Entity name
            task_name: Task name
            version_number: Version number

        Returns:
            Created published file dictionary
        """
        file_stem = Path(file_path).stem

        # Published file name and code
        version_str = f"v{version_number:03d}"
        published_name = f"{entity_name}_{task_name}_{version_str}"
        published_code = f"{file_stem}.{version_str}"

        try:
            published_file = self.published_file_manager.create_published_file(
                version_id=version_id,
                version_number=version_number,
                task_id=task_id,
                name=published_name,
                file_code=published_code,
                project_id=project_id,
                description=description
            )

            return published_file

        except Exception as e:
            raise PublishingError(f"Failed to create published file: {str(e)}") from e

    def update_attachment_links(
        self,
        attachment_id: int,
        task_id: int,
        version_id: int,
        published_file_id: int,
        file_path: str
    ) -> Dict:
        """
        Update attachment with task, version, published file links and metadata.

        Args:
            attachment_id: Attachment ID to update
            task_id: Task ID to link
            version_id: Version ID to link
            published_file_id: PublishedFile ID to link
            file_path: File path (for extracting filename and extension)

        Returns:
            Updated attachment dictionary
        """
        # Extract file info
        file_path_obj = Path(file_path)
        original_filename = file_path_obj.name
        # Build update data
        update_data = {
            'original_fname': original_filename,
            'attachment_links': [
                {'type': 'Task', 'id': task_id},
                {'type': 'Version', 'id': version_id},
                {'type': 'PublishedFile', 'id': published_file_id}
            ]
        }

        try:
            updated_attachment = self.attachment_manager.update_entity(
                entity_id=attachment_id,
                data=update_data
            )

            return updated_attachment

        except Exception as e:
            raise PublishingError(f"Failed to update attachment metadata: {str(e)}") from e

    def set_task_to_review(self, task_id: int) -> Dict:
        """
        Set task status to 'rev' (Pending Review).

        Args:
            task_id: Task ID to update

        Returns:
            Updated task dictionary
        """
        try:
            updated_task = self.task_manager.update_entity(
                entity_id=task_id,
                data={'sg_status_list': 'rev'}
            )

            return updated_task

        except Exception as e:
            raise PublishingError(f"Failed to update task status: {str(e)}") from e


if __name__ == "__main__":
    """Test publishing service"""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Initialize connection
    sg_instance = ShotgridInstance()
    sg_instance.connect()

    # Example: Initialize with task dictionary (from cache)
    # asset_task = {
    #     'type': 'Task', 'id': 5947, 'content': '002_Modeling', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 
    #     'entity': {'id': 1480, 'name': 'generic_prop_1', 'type': 'Asset'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': []
    # }

    # shot_task = {
    #     'type': 'Task', 'id': 6078, 'content': '02_Animacion', 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'due_date': None, 'sg_priority_1': None, 
    #     'entity': {'id': 1209, 'name': 'sq010_050', 'type': 'Shot'}, 
    #     'sg_status_list': 'wtg', 'task_assignees': []
    # }

    publish_service = PublishingService(shotgun_instance=sg_instance)
    
    # publish_service.publish(5947, "/mnt/c/Projects/kukari_projects/CianLu_V02.abc", "test publish tool", set_task_to_review=False)
    # publish_service.publish_multiple(
    #         task_id=5947, 
    #         file_paths=[
    #                 "/mnt/c/Projects/kukari_projects/CianLu_Body_Color.1005.png",
    #                 "/mnt/c/Projects/kukari_projects/CianLu_Body_Color.1001.png",
    #                 "/mnt/c/Projects/kukari_projects/CianLu_Body_Color.1002.png",
    #                 "/mnt/c/Projects/kukari_projects/CianLu_Body_Color.1003.png"
    #             ],
    #         set_task_to_review=False
    #     )

    logger.info("Publishing service module loaded successfully")
    sg_instance.disconnect()
