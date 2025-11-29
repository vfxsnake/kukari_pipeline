"""
Zip Utility for Shotgrid Manager

Provides cross-platform folder compression functionality for publishing workflows.
Uses Python's built-in zipfile module (Windows, Linux, Mac compatible).
"""

import os
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class ZipUtility:
    """
    Cross-platform utility for creating zip archives.

    Designed for publishing workflows where folders need to be compressed
    before uploading to ShotGrid.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def zip_folder(
        self,
        folder_path: str,
        output_path: Optional[str] = None,
        compression: int = zipfile.ZIP_DEFLATED,
        exclude_patterns: Optional[List[str]] = None
    ) -> str:
        """
        Create a zip archive from a folder.

        Args:
            folder_path: Path to folder to compress
            output_path: Optional output path for zip file. If not provided,
                        creates zip in temp directory with timestamp
            compression: Compression method (ZIP_DEFLATED, ZIP_STORED, ZIP_BZIP2, ZIP_LZMA)
            exclude_patterns: Optional list of patterns to exclude (e.g., ['*.tmp', '__pycache__'])

        Returns:
            Path to created zip file

        Raises:
            FileNotFoundError: If folder_path doesn't exist
            ValueError: If folder_path is not a directory
            IOError: If zip creation fails

        Example:
            >>> zipper = ZipUtility()
            >>> zip_path = zipper.zip_folder("/path/to/folder")
            >>> print(f"Created: {zip_path}")
        """
        # Validate input
        folder_path = os.path.abspath(folder_path)

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"Path is not a directory: {folder_path}")

        # Determine output path
        if output_path is None:
            # Create in temp directory with timestamp
            folder_name = os.path.basename(folder_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{folder_name}_{timestamp}.zip"
            output_path = os.path.join(tempfile.gettempdir(), zip_filename)
        else:
            output_path = os.path.abspath(output_path)
            # Ensure .zip extension
            if not output_path.endswith('.zip'):
                output_path += '.zip'

        # Prepare exclude patterns
        exclude_patterns = exclude_patterns or []

        self.logger.info(f"Creating zip archive: {output_path}")
        self.logger.info(f"Source folder: {folder_path}")

        try:
            # Create zip file
            with zipfile.ZipFile(output_path, 'w', compression) as zipf:
                # Walk through directory
                file_count = 0
                excluded_count = 0

                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)

                        # Check if file should be excluded
                        if self._should_exclude(file_path, exclude_patterns):
                            excluded_count += 1
                            self.logger.debug(f"Excluding: {file_path}")
                            continue

                        # Calculate archive name (relative path from folder)
                        arcname = os.path.relpath(file_path, folder_path)

                        # Add to zip
                        zipf.write(file_path, arcname)
                        file_count += 1

                        if file_count % 100 == 0:
                            self.logger.debug(f"Compressed {file_count} files...")

            # Get zip file size
            zip_size = os.path.getsize(output_path)
            zip_size_mb = zip_size / (1024 * 1024)

            self.logger.info(f"✓ Zip created successfully!")
            self.logger.info(f"  - Files: {file_count}")
            self.logger.info(f"  - Excluded: {excluded_count}")
            self.logger.info(f"  - Size: {zip_size_mb:.2f} MB")
            self.logger.info(f"  - Path: {output_path}")

            return output_path

        except Exception as e:
            self.logger.error(f"Failed to create zip archive: {e}")
            # Clean up partial zip file if it exists
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise IOError(f"Failed to create zip archive: {str(e)}") from e

    def zip_file(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        compression: int = zipfile.ZIP_DEFLATED
    ) -> str:
        """
        Create a zip archive from a single file.

        Args:
            file_path: Path to file to compress
            output_path: Optional output path for zip file
            compression: Compression method

        Returns:
            Path to created zip file
        """
        # Validate input
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        # Determine output path
        if output_path is None:
            # Create in temp directory
            file_name = os.path.basename(file_path)
            file_stem = os.path.splitext(file_name)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{file_stem}_{timestamp}.zip"
            output_path = os.path.join(tempfile.gettempdir(), zip_filename)
        else:
            output_path = os.path.abspath(output_path)
            if not output_path.endswith('.zip'):
                output_path += '.zip'

        self.logger.info(f"Creating zip archive from file: {file_path}")

        try:
            with zipfile.ZipFile(output_path, 'w', compression) as zipf:
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)

            zip_size = os.path.getsize(output_path)
            zip_size_mb = zip_size / (1024 * 1024)

            self.logger.info(f"✓ Zip created: {output_path} ({zip_size_mb:.2f} MB)")

            return output_path

        except Exception as e:
            self.logger.error(f"Failed to create zip: {e}")
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise IOError(f"Failed to create zip: {str(e)}") from e

    def _should_exclude(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """
        Check if file should be excluded based on patterns.

        Args:
            file_path: File path to check
            exclude_patterns: List of patterns (supports wildcards)

        Returns:
            True if file should be excluded
        """
        if not exclude_patterns:
            return False

        file_path_obj = Path(file_path)

        for pattern in exclude_patterns:
            # Check if pattern matches filename or any parent directory
            if file_path_obj.match(pattern):
                return True

            # Check each part of the path
            for part in file_path_obj.parts:
                if Path(part).match(pattern):
                    return True

        return False

    def get_zip_info(self, zip_path: str) -> dict:
        """
        Get information about a zip file.

        Args:
            zip_path: Path to zip file

        Returns:
            Dictionary with zip file information
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Zip file not found: {zip_path}")

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            info_list = zipf.infolist()

            total_uncompressed = sum(info.file_size for info in info_list)
            total_compressed = sum(info.compress_size for info in info_list)

            return {
                'path': zip_path,
                'file_count': len(info_list),
                'compressed_size': total_compressed,
                'compressed_size_mb': total_compressed / (1024 * 1024),
                'uncompressed_size': total_uncompressed,
                'uncompressed_size_mb': total_uncompressed / (1024 * 1024),
                'compression_ratio': (1 - total_compressed / total_uncompressed) * 100 if total_uncompressed > 0 else 0,
                'files': [info.filename for info in info_list]
            }


# Convenience functions for quick use
def zip_folder(folder_path: str, output_path: Optional[str] = None, **kwargs) -> str:
    """
    Quick function to zip a folder.

    Args:
        folder_path: Path to folder to compress
        output_path: Optional output path
        **kwargs: Additional arguments for ZipUtility.zip_folder()

    Returns:
        Path to created zip file
    """
    zipper = ZipUtility()
    return zipper.zip_folder(folder_path, output_path, **kwargs)


def zip_file(file_path: str, output_path: Optional[str] = None, **kwargs) -> str:
    """
    Quick function to zip a file.

    Args:
        file_path: Path to file to compress
        output_path: Optional output path
        **kwargs: Additional arguments for ZipUtility.zip_file()

    Returns:
        Path to created zip file
    """
    zipper = ZipUtility()
    return zipper.zip_file(file_path, output_path, **kwargs)


if __name__ == "__main__":
    """Test zip utility"""
    from utils.logger import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Test zip utility
    zipper = ZipUtility()

    # Example: Zip a folder
    folder_to_zip = "/mnt/c/Projects/kukari_projects/folder_test"
    try:
        zip_path = zipper.zip_folder(
            folder_path=folder_to_zip,
            output_path=folder_to_zip,
            exclude_patterns=['*.tmp', '__pycache__', '*.pyc']
        )
    
        # Get info about created zip
        info = zipper.get_zip_info(zip_path)
        logger.info(f"Zip info: {info}")
    
    except Exception as e:
        logger.error(f"Zip failed: {e}")

    logger.info("Zip utility loaded successfully")
