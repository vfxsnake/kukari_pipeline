"""
Download Service for Shotgrid Manager

Handles downloading files from ShotGrid with proper path structure and naming.

Flow:
    Version → PublishedFiles → Attachments → Download

File naming: {Entity}_{Task}_{version:03d}.{extension}
Path structure: /WORK_AREA/Project/ASSETS|SHOTS/Entity/Task/
"""

import logging
import os
from typing import List, Dict, Optional, Callable
from pathlib import Path

from core.shotgrid_instance import ShotgridInstance
from core.attachment_manager import AttachmentManager
from core.published_file_manager import PublishedFileManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging


class DownloadService:
    """
    Service for downloading files from ShotGrid.

    Handles complete download flow:
    - Query attachments from published files
    - Build structured destination paths
    - Standardize file naming
    - Download files with progress tracking
    """

    def __init__(self, shotgrid_instance: ShotgridInstance):
        """
        Initialize download service.

        Args:
            shotgrid_instance: ShotgridInstance with active connection
        """
        self.shotgrid_instance = shotgrid_instance
        self.logger = logging.getLogger(__name__)
        setup_logging()

        # Initialize managers
        self.attachment_manager = AttachmentManager(shotgrid_instance)
        self.published_file_manager = PublishedFileManager(shotgrid_instance)
        self.path_builder = PathBuilder(shotgrid_instance)

    # ========================================================================
    # Public API
    # ========================================================================

    def download_version(
        self,
        version: Dict,
        task_data: Dict,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Download all files from a version.

        Args:
            version: Version dictionary with id, code, published_files
            task_data: Task dictionary with id, content, entity, project
            progress_callback: Optional callback(current, total, filename)

        Returns:
            List of downloaded file paths

        Raises:
            Exception: If download fails
        """
        version_id = version.get('id', -1)
        version_code = version.get('code', 'unknown')

        self.logger.info(f"Starting download for version {version_id} ({version_code})")

        # Get all published files from version
        published_files = version.get('published_files', [])

        if not published_files:
            self.logger.warning(f"Version {version_id} has no published files")
            return []

        self.logger.info(f"Found {len(published_files)} published files")

        # Download files from all published files
        downloaded_paths = []
        total_files = 0

        # First, count total attachments
        for pub_file in published_files:
            attachments = self._get_attachments_for_published_file(pub_file)
            total_files += len(attachments)

        current_file = 0

        for pub_file in published_files:
            try:
                paths = self._download_published_file(
                    pub_file,
                    version,
                    task_data,
                    progress_callback,
                    current_file,
                    total_files
                )
                downloaded_paths.extend(paths)
                current_file += len(paths)

            except Exception as e:
                self.logger.error(
                    f"Failed to download published file {pub_file.get('id')}: {e}",
                    exc_info=True
                )
                # Continue with other files

        self.logger.info(
            f"Download complete: {len(downloaded_paths)} files downloaded"
        )
        return downloaded_paths

    def download_published_file(
        self,
        pub_file: Dict,
        version: Dict,
        task_data: Dict,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Download files from a single published file.

        Args:
            pub_file: PublishedFile dictionary
            version: Version dictionary (for naming)
            task_data: Task dictionary (for path building)
            progress_callback: Optional callback(current, total, filename)

        Returns:
            List of downloaded file paths
        """
        return self._download_published_file(
            pub_file,
            version,
            task_data,
            progress_callback,
            0,
            1
        )

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _download_published_file(
        self,
        pub_file: Dict,
        version: Dict,
        task_data: Dict,
        progress_callback: Optional[Callable[[int, int, str], None]],
        current_offset: int,
        total_files: int
    ) -> List[str]:
        """
        Download all attachments from a published file.

        Args:
            pub_file: PublishedFile dictionary
            version: Version dictionary
            task_data: Task dictionary
            progress_callback: Progress callback
            current_offset: Current file index offset
            total_files: Total number of files

        Returns:
            List of downloaded file paths
        """
        pub_file_id = pub_file.get('id', -1)
        pub_file_name = pub_file.get('name', 'Unknown')

        self.logger.debug(f"Processing published file {pub_file_id}: {pub_file_name}")

        # Get attachments for this published file
        attachments = self._get_attachments_for_published_file(pub_file)

        if not attachments:
            self.logger.warning(
                f"Published file {pub_file_id} has no attachments"
            )
            return []

        self.logger.info(
            f"Found {len(attachments)} attachments for {pub_file_name}"
        )

        # Download each attachment
        downloaded_paths = []

        for i, attachment in enumerate(attachments):
            try:
                file_path = self._download_attachment(
                    attachment,
                    version,
                    task_data
                )

                if file_path:
                    downloaded_paths.append(file_path)

                    # Report progress
                    if progress_callback:
                        current = current_offset + i + 1
                        filename = os.path.basename(file_path)
                        progress_callback(current, total_files, filename)

            except Exception as e:
                self.logger.error(
                    f"Failed to download attachment {attachment.get('id')}: {e}",
                    exc_info=True
                )
                # Continue with other attachments

        return downloaded_paths

    def _get_attachments_for_published_file(self, pub_file: Dict) -> List[Dict]:
        """
        Get all attachments linked to a published file.

        Args:
            pub_file: PublishedFile dictionary with id

        Returns:
            List of attachment dictionaries
        """
        pub_file_id = pub_file.get('id', -1)

        if pub_file_id == -1:
            self.logger.error("Invalid published file ID")
            return []

        try:
            # Query attachments linked to this published file
            attachments = self.attachment_manager.get_entities(
                filters=[
                    ['attachment_links', 'in', [
                        {'type': 'PublishedFile', 'id': pub_file_id}
                    ]]
                ],
                fields=[
                    'id', 'this_file', 'original_fname',
                    'file_extension', 'filename'
                ]
            )

            return attachments

        except Exception as e:
            self.logger.error(
                f"Failed to query attachments for published file {pub_file_id}: {e}"
            )
            return []

    def _download_attachment(
        self,
        attachment: Dict,
        version: Dict,
        task_data: Dict
    ) -> Optional[str]:
        """
        Download a single attachment to structured path.

        Args:
            attachment: Attachment dictionary
            version: Version dictionary (for naming)
            task_data: Task dictionary (for path)

        Returns:
            Downloaded file path, or None if failed
        """
        attachment_id = attachment.get('id', -1)

        if attachment_id == -1:
            self.logger.error("Invalid attachment ID")
            return None

        # Build destination path
        dest_path = self._build_download_path(attachment, version, task_data)

        if not dest_path:
            self.logger.error("Failed to build download path")
            return None

        # Ensure directory exists
        dest_dir = os.path.dirname(dest_path)
        try:
            self.path_builder.create_path(dest_dir)
        except Exception as e:
            self.logger.error(f"Failed to create directory {dest_dir}: {e}")
            return None

        # Download file
        try:
            self.logger.info(f"Downloading attachment {attachment_id} to {dest_path}")

            self.attachment_manager.download_attachment(
                attachment_id=attachment_id,
                target_path=dest_path
            )

            # Verify file was downloaded
            if os.path.exists(dest_path):
                file_size = os.path.getsize(dest_path)
                self.logger.info(
                    f"✓ Downloaded {os.path.basename(dest_path)} ({file_size} bytes)"
                )
                return dest_path
            else:
                self.logger.error(f"File not found after download: {dest_path}")
                return None

        except Exception as e:
            self.logger.error(
                f"Failed to download attachment {attachment_id}: {e}",
                exc_info=True
            )
            return None

    def _build_download_path(
        self,
        attachment: Dict,
        version: Dict,
        task_data: Dict
    ) -> Optional[str]:
        """
        Build standardized download path for attachment.

        Path: /WORK_AREA/Project/ASSETS|SHOTS/Entity/Task/
        Name: {Entity}_{Task}_{version:03d}.{extension}

        Args:
            attachment: Attachment dictionary
            version: Version dictionary
            task_data: Task dictionary

        Returns:
            Full file path, or None if unable to build
        """
        # Get task path from PathBuilder
        task_id = task_data.get('id', -1)

        if task_id == -1:
            self.logger.error("Invalid task ID")
            return None

        task_path = self.path_builder.get_path_from_task(task_id)

        if not task_path:
            self.logger.error(f"Failed to build path for task {task_id}")
            return None

        # Build standardized filename
        filename = self._build_filename(attachment, version, task_data)

        if not filename:
            self.logger.error("Failed to build filename")
            return None

        # Combine path and filename
        full_path = os.path.join(task_path, filename)

        return full_path

    def _build_filename(
        self,
        attachment: Dict,
        version: Dict,
        task_data: Dict
    ) -> Optional[str]:
        """
        Build standardized filename.

        Format: {Entity}_{Task}_{version:03d}.{extension}
        Example: Cianlu_Rig_v005.ma

        Args:
            attachment: Attachment dictionary
            version: Version dictionary
            task_data: Task dictionary

        Returns:
            Filename string, or None if unable to build
        """
        # Extract components
        entity = task_data.get('entity', {})
        entity_name = entity.get('name', '')

        task_content = task_data.get('content', '')

        # Extract version number from version code
        version_code = version.get('code', '')
        version_number = self._extract_version_number(version_code)

        # Get file extension from attachment
        extension = attachment.get('file_extension', '')

        # If no extension in attachment, try to get from original filename
        if not extension:
            original_fname = attachment.get('original_fname', '')
            if original_fname and '.' in original_fname:
                extension = original_fname.split('.')[-1]

        # Validate components
        if not entity_name or not task_content:
            self.logger.error(
                f"Missing entity name or task content: "
                f"entity={entity_name}, task={task_content}"
            )
            return None

        # Build filename
        if extension:
            filename = f"{entity_name}_{task_content}_v{version_number:03d}.{extension}"
        else:
            # No extension - use original filename as fallback
            original_fname = attachment.get('original_fname', 'file')
            filename = f"{entity_name}_{task_content}_v{version_number:03d}_{original_fname}"

        self.logger.debug(f"Built filename: {filename}")
        return filename

    def _extract_version_number(self, version_code: str) -> int:
        """
        Extract version number from version code.

        Examples:
            "Cianlu_Rig_v005" → 5
            "v003" → 3
            "some_v010_name" → 10

        Args:
            version_code: Version code string

        Returns:
            Version number as integer, defaults to 1 if not found
        """
        import re

        # Look for pattern "v" followed by digits
        match = re.search(r'v(\d+)', version_code, re.IGNORECASE)

        if match:
            return int(match.group(1))

        self.logger.warning(
            f"Could not extract version number from '{version_code}', using 1"
        )
        return 1


if __name__ == "__main__":
    """Test download service."""
    from core.shotgrid_instance import ShotgridInstance
    from core.task_manager import TaskManager
    from core.version_manger import VersionManager

    setup_logging()
    logger = logging.getLogger(__name__)

    # Connect to ShotGrid
    sg_instance = ShotgridInstance()
    sg_instance.connect()

    # Create service
    download_service = DownloadService(sg_instance)

    # Get a task and version for testing
    task_manager = TaskManager(sg_instance)
    version_manager = VersionManager(sg_instance)

    # Test with task 5947 (Modeling on generic_prop_1)
    task_id = 5947
    task = task_manager.get_task(task_id)

    if task:
        logger.info(f"Task: {task.get('content')} on {task.get('entity', {}).get('name')}")

        # Get latest version
        versions = version_manager.get_versions_from_task(task_id)

        if versions:
            latest_version = versions[0]
            logger.info(f"Latest version: {latest_version.get('code')}")

            # Progress callback
            def progress(current, total, filename):
                logger.info(f"[{current}/{total}] Downloading: {filename}")

            # Download version
            try:
                downloaded_files = download_service.download_version(
                    version=latest_version,
                    task_data=task,
                    progress_callback=progress
                )

                logger.info(f"\n{'='*60}")
                logger.info(f"Download complete!")
                logger.info(f"Files downloaded: {len(downloaded_files)}")
                for path in downloaded_files:
                    logger.info(f"  - {path}")
                logger.info(f"{'='*60}")

            except Exception as e:
                logger.error(f"Download failed: {e}", exc_info=True)
        else:
            logger.warning("No versions found")
    else:
        logger.error("Task not found")

    # Disconnect
    sg_instance.disconnect()
