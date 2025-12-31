"""
Dependencies Dialog for Shotgrid Manager

Displays task dependencies in a tree view with:
- Upstream task dependencies
- Asset dependencies (for shot tasks)
- All versions for each dependency (expandable)
- Published files for each version
- Download actions for files
"""

import logging
import os
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QMessageBox,
    QProgressDialog, QApplication, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon

from core.version_manger import VersionManager
from core.dependency_resolver import EXCLUDED_VERSION_STATUSES
from core.download_service import DownloadService


class DependenciesDialog(QDialog):
    """
    Dialog for viewing task dependencies.

    Features:
    - Tree view of upstream tasks and asset dependencies
    - Expandable versions (show all versions, not just latest)
    - Published files display
    - Download actions (Download All, Download Latest, Download Selected)
    - Fallback indicators for asset dependencies
    """

    # Signal emitted when files are downloaded
    files_downloaded = Signal(list)  # Emits list of downloaded file paths

    def __init__(
        self,
        task_data: Dict,
        dependencies: List[Dict],
        version_manager: VersionManager,
        parent=None
    ):
        """
        Initialize dependencies dialog.

        Args:
            task_data: Task dictionary with id, content, entity, project
            dependencies: List of dependency dicts from DependencyResolver
            version_manager: VersionManager instance for loading all versions
            parent: Parent widget
        """
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self.task_data = task_data
        self.dependencies = dependencies
        self.version_manager = version_manager

        # Initialize download service
        self.download_service = DownloadService(version_manager.manager)

        # Extract task info
        self.task_id = task_data.get('id', -1)
        self.task_name = task_data.get('content', 'Unknown Task')
        self.entity_data = task_data.get('entity', {})
        self.entity_name = self.entity_data.get('name', 'Unknown')
        self.entity_type = self.entity_data.get('type', 'Entity')

        # Track expanded dependencies (task_id -> versions list)
        self.expanded_versions = {}

        self._setup_ui()
        self._populate_tree()
        self._apply_style()

    # ========================================================================
    # UI Setup
    # ========================================================================

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("View Dependencies")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Task info section
        info_group = self._create_info_section()
        layout.addWidget(info_group)

        # Dependencies tree section
        tree_group = self._create_tree_section()
        layout.addWidget(tree_group)

        # Action buttons
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)

    def _create_info_section(self) -> QGroupBox:
        """Create task info section."""
        group = QGroupBox("Dependencies For")
        layout = QVBoxLayout(group)

        # Task info
        task_label = QLabel(f"<b>Task:</b> {self.task_name}")
        layout.addWidget(task_label)

        # Entity info
        entity_label = QLabel(f"<b>Entity:</b> {self.entity_type}: {self.entity_name}")
        layout.addWidget(entity_label)

        # Dependency count
        count_label = QLabel(f"<b>Total Dependencies:</b> {len(self.dependencies)}")
        layout.addWidget(count_label)

        return group

    def _create_tree_section(self) -> QGroupBox:
        """Create dependencies tree section."""
        group = QGroupBox("Dependency Tree")
        layout = QVBoxLayout(group)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Dependency / Version / File", "Status", "Info"])
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 250)

        # Enable context menu
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        # Connect expansion signal
        self.tree.itemExpanded.connect(self._on_item_expanded)

        layout.addWidget(self.tree)

        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()

        # Download All button
        self.download_all_btn = QPushButton("Download All Latest")
        self.download_all_btn.clicked.connect(self._download_all_latest)
        layout.addWidget(self.download_all_btn)

        # Download All Versions button
        self.download_all_versions_btn = QPushButton("Download All Versions")
        self.download_all_versions_btn.clicked.connect(self._download_all_versions)
        layout.addWidget(self.download_all_versions_btn)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        return layout

    # ========================================================================
    # Tree Population
    # ========================================================================

    def _populate_tree(self):
        """Populate tree with dependencies."""
        if not self.dependencies:
            no_deps_item = QTreeWidgetItem(self.tree, ["No dependencies found", "", ""])
            no_deps_item.setForeground(0, Qt.gray)
            return

        # Group dependencies by source
        upstream_deps = [d for d in self.dependencies if d.get('source') == 'upstream_task']
        asset_deps = [d for d in self.dependencies if d.get('source') == 'asset_dependency']

        # Add upstream tasks
        if upstream_deps:
            upstream_root = QTreeWidgetItem(
                self.tree,
                [f"Upstream Tasks ({len(upstream_deps)})", "", ""]
            )
            upstream_root.setExpanded(True)
            upstream_root.setData(0, Qt.UserRole, {'type': 'category'})

            for dep in upstream_deps:
                self._add_dependency_item(upstream_root, dep)

        # Add asset dependencies
        if asset_deps:
            asset_root = QTreeWidgetItem(
                self.tree,
                [f"Asset Dependencies ({len(asset_deps)})", "", ""]
            )
            asset_root.setExpanded(True)
            asset_root.setData(0, Qt.UserRole, {'type': 'category'})

            for dep in asset_deps:
                self._add_dependency_item(asset_root, dep)

    def _add_dependency_item(self, parent: QTreeWidgetItem, dep: Dict):
        """
        Add a dependency item to the tree.

        Args:
            parent: Parent tree item
            dep: Dependency dictionary
        """
        # Get task info
        task = dep.get('task', {})
        task_id = task.get('id', -1)
        task_content = task.get('content', 'Unknown')
        entity = dep.get('entity', {})
        entity_name = entity.get('name', 'Unknown')
        entity_type = entity.get('type', 'Entity')
        step = dep.get('step', {})
        step_name = step.get('name', 'Unknown Step')

        # Build label
        label = f"{entity_type}: {entity_name} - {step_name}"

        # Check for fallback
        is_fallback = dep.get('is_fallback', False)
        if is_fallback:
            preferred = dep.get('preferred_step', '')
            actual = dep.get('actual_step', '')
            label += f" [Using {actual} - {preferred} not available]"

        # Create task item
        task_item = QTreeWidgetItem(parent, [label, "", task_content])
        task_item.setData(0, Qt.UserRole, {
            'type': 'task',
            'task_id': task_id,
            'dependency': dep
        })

        # Add warning if present
        warning = dep.get('version_warning')
        if warning:
            warning_item = QTreeWidgetItem(task_item, [f"⚠ {warning}", "No Version", ""])
            warning_item.setForeground(0, Qt.yellow)
            warning_item.setData(0, Qt.UserRole, {'type': 'warning'})

        # Add latest version if available
        version = dep.get('version')
        if version:
            self._add_version_item(task_item, version, is_latest=True)

        # Add placeholder for "Load All Versions"
        load_item = QTreeWidgetItem(
            task_item,
            ["▶ Click to load all versions...", "", ""]
        )
        load_item.setForeground(0, Qt.gray)
        load_item.setData(0, Qt.UserRole, {
            'type': 'load_versions_placeholder',
            'task_id': task_id
        })

    def _add_version_item(
        self,
        parent: QTreeWidgetItem,
        version: Dict,
        is_latest: bool = False
    ):
        """
        Add a version item to the tree.

        Args:
            parent: Parent tree item
            version: Version dictionary
            is_latest: Whether this is the latest version
        """
        version_id = version.get('id', -1)
        version_code = version.get('code', 'Unknown')
        version_status = version.get('sg_status_list', 'N/A')
        created_at = version.get('created_at', '')

        # Format created date
        created_str = ""
        if created_at:
            if hasattr(created_at, 'strftime'):
                created_str = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                created_str = str(created_at)

        # Build label with latest indicator
        label = version_code
        if is_latest:
            label += " ⭐ (Latest)"

        # Create version item
        version_item = QTreeWidgetItem(
            parent,
            [label, version_status, created_str]
        )
        version_item.setData(0, Qt.UserRole, {
            'type': 'version',
            'version_id': version_id,
            'version': version
        })

        # Add published files
        published_files = version.get('published_files', [])
        if published_files:
            for pub_file in published_files:
                self._add_published_file_item(version_item, pub_file)
        else:
            no_files_item = QTreeWidgetItem(
                version_item,
                ["No published files", "", ""]
            )
            no_files_item.setForeground(0, Qt.gray)
            no_files_item.setData(0, Qt.UserRole, {'type': 'no_files'})

    def _add_published_file_item(self, parent: QTreeWidgetItem, pub_file: Dict):
        """
        Add a published file item to the tree.

        Args:
            parent: Parent tree item (version)
            pub_file: Published file dictionary
        """
        file_id = pub_file.get('id', -1)
        file_name = pub_file.get('name', 'Unknown File')
        file_type = pub_file.get('type', 'PublishedFile')

        # Create file item
        file_item = QTreeWidgetItem(parent, [f"📄 {file_name}", "File", ""])
        file_item.setData(0, Qt.UserRole, {
            'type': 'published_file',
            'file_id': file_id,
            'file': pub_file
        })

    # ========================================================================
    # Version Expansion
    # ========================================================================

    @Slot(QTreeWidgetItem)
    def _on_item_expanded(self, item: QTreeWidgetItem):
        """
        Handle item expansion - load all versions if needed.

        Args:
            item: Expanded tree item
        """
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')

        # If this is a task item, check if we need to load versions
        if item_type == 'task':
            task_id = data.get('task_id', -1)

            # Check if we already loaded versions
            if task_id in self.expanded_versions:
                return

            # Find the placeholder item
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.UserRole)
                if child_data and child_data.get('type') == 'load_versions_placeholder':
                    # Replace placeholder with all versions
                    self._load_all_versions(item, task_id, child)
                    break

    def _load_all_versions(
        self,
        task_item: QTreeWidgetItem,
        task_id: int,
        placeholder_item: QTreeWidgetItem
    ):
        """
        Load all versions for a task.

        Args:
            task_item: Task tree item
            task_id: Task ID
            placeholder_item: Placeholder item to replace
        """
        try:
            # Query all versions (excluding rejected/omitted)
            versions = self.version_manager.get_entities(
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

            # Remove placeholder
            index = task_item.indexOfChild(placeholder_item)
            task_item.removeChild(placeholder_item)

            # Add all versions (skip first one if it's already shown as latest)
            # Check if first child is already a version
            first_child_data = task_item.child(0).data(0, Qt.UserRole) if task_item.childCount() > 0 else None
            skip_first = first_child_data and first_child_data.get('type') == 'version'

            start_index = 1 if skip_first else 0

            if start_index < len(versions):
                # Add remaining versions at the position where placeholder was
                for i, version in enumerate(versions[start_index:]):
                    self._add_version_item(task_item, version, is_latest=False)
            else:
                # No additional versions
                no_more_item = QTreeWidgetItem(
                    task_item,
                    ["No additional versions", "", ""]
                )
                no_more_item.setForeground(0, Qt.gray)

            # Mark as expanded
            self.expanded_versions[task_id] = versions

            self.logger.info(f"Loaded {len(versions)} versions for task {task_id}")

        except Exception as e:
            self.logger.error(f"Error loading versions for task {task_id}: {e}", exc_info=True)
            # Show error in tree
            error_item = QTreeWidgetItem(
                task_item,
                [f"Error loading versions: {str(e)}", "", ""]
            )
            error_item.setForeground(0, Qt.red)

    # ========================================================================
    # Context Menu
    # ========================================================================

    @Slot(object)
    def _show_context_menu(self, position):
        """
        Show context menu for tree items.

        Args:
            position: Menu position
        """
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')

        menu = QMenu(self)

        # Context menu for version items
        if item_type == 'version':
            # Get task data from parent item
            parent_item = item.parent()
            if parent_item:
                parent_data = parent_item.data(0, Qt.UserRole)
                if parent_data and parent_data.get('type') == 'task':
                    dependency = parent_data.get('dependency', {})
                    task = dependency.get('task', {})
                    version = data.get('version')

                    download_action = QAction("Download This Version", self)
                    download_action.triggered.connect(
                        lambda: self._download_single_version(version, task)
                    )
                    menu.addAction(download_action)

        # Context menu for published file items
        elif item_type == 'published_file':
            # For now, download the whole version (files are grouped by version)
            # We could implement individual file download later
            parent_item = item.parent()
            if parent_item:
                parent_data = parent_item.data(0, Qt.UserRole)
                if parent_data and parent_data.get('type') == 'version':
                    # Get task from grandparent
                    grandparent_item = parent_item.parent()
                    if grandparent_item:
                        grandparent_data = grandparent_item.data(0, Qt.UserRole)
                        if grandparent_data and grandparent_data.get('type') == 'task':
                            dependency = grandparent_data.get('dependency', {})
                            task = dependency.get('task', {})
                            version = parent_data.get('version')

                            download_action = QAction("Download Parent Version", self)
                            download_action.triggered.connect(
                                lambda: self._download_single_version(version, task)
                            )
                            menu.addAction(download_action)

        # Context menu for task items
        elif item_type == 'task':
            download_latest_action = QAction("Download Latest Version", self)
            download_latest_action.triggered.connect(
                lambda: self._download_task_latest(data.get('dependency'))
            )
            menu.addAction(download_latest_action)

        if menu.actions():
            menu.exec_(self.tree.viewport().mapToGlobal(position))

    # ========================================================================
    # Download Actions
    # ========================================================================

    @Slot()
    def _download_all_latest(self):
        """Download all latest versions from dependencies."""
        self.logger.info("Download all latest versions requested")

        # Collect versions to download
        versions_to_download = []

        for dep in self.dependencies:
            version = dep.get('version')
            if version:
                versions_to_download.append({
                    'version': version,
                    'task': dep.get('task', {})
                })

        if not versions_to_download:
            QMessageBox.information(
                self,
                "No Files",
                "No files available to download in latest versions."
            )
            return

        # Download all versions with progress
        self._download_multiple_versions(
            versions_to_download,
            f"Download All Latest ({len(versions_to_download)} versions)"
        )

    @Slot()
    def _download_all_versions(self):
        """Download all files from all versions of all dependencies."""
        self.logger.info("Download all versions requested")

        # TODO: Implement downloading all versions
        # This would require expanding all tasks and collecting all files
        QMessageBox.information(
            self,
            "Not Implemented",
            "Download All Versions feature coming soon.\n\n"
            "For now, please expand individual tasks and download specific versions."
        )

    def _download_task_latest(self, dependency: Dict):
        """
        Download latest version from a dependency.

        Args:
            dependency: Dependency dictionary
        """
        version = dependency.get('version')
        task = dependency.get('task', {})

        if not version:
            QMessageBox.warning(
                self,
                "No Version",
                "No version available for this dependency."
            )
            return

        self._download_single_version(version, task)

    def _download_single_version(self, version: Dict, task_data: Dict):
        """
        Download all files from a single version.

        Args:
            version: Version dictionary
            task_data: Task dictionary for path building
        """
        published_files = version.get('published_files', [])

        if not published_files:
            QMessageBox.information(
                self,
                "No Files",
                f"Version {version.get('code')} has no published files."
            )
            return

        version_code = version.get('code', 'Unknown')

        # Create progress dialog
        progress = QProgressDialog(
            f"Downloading version {version_code}...",
            "Cancel",
            0,
            100,
            self
        )
        progress.setWindowTitle("Downloading Files")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        QApplication.processEvents()

        try:
            downloaded_files = []

            # Progress callback
            def update_progress(current, total, filename):
                if progress.wasCanceled():
                    raise Exception("Download canceled by user")

                progress.setMaximum(total)
                progress.setValue(current)
                progress.setLabelText(f"Downloading {filename}... ({current}/{total})")
                QApplication.processEvents()

            # Download version
            downloaded_files = self.download_service.download_version(
                version=version,
                task_data=task_data,
                progress_callback=update_progress
            )

            progress.close()

            # Show success message
            if downloaded_files:
                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"Successfully downloaded {len(downloaded_files)} file(s) from {version_code}:\n\n" +
                    "\n".join(f"  • {os.path.basename(f)}" for f in downloaded_files[:5]) +
                    (f"\n  ... and {len(downloaded_files) - 5} more" if len(downloaded_files) > 5 else "")
                )

                # Emit signal
                self.files_downloaded.emit(downloaded_files)
            else:
                QMessageBox.warning(
                    self,
                    "No Files Downloaded",
                    "No files were downloaded. Check logs for details."
                )

        except Exception as e:
            progress.close()
            self.logger.error(f"Download failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Download Failed",
                f"Failed to download files:\n{str(e)}"
            )

    def _download_multiple_versions(
        self,
        versions_data: List[Dict],
        title: str
    ):
        """
        Download multiple versions with combined progress.

        Args:
            versions_data: List of {'version': dict, 'task': dict}
            title: Progress dialog title
        """
        # Create progress dialog
        progress = QProgressDialog(
            "Preparing download...",
            "Cancel",
            0,
            100,
            self
        )
        progress.setWindowTitle(title)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        QApplication.processEvents()

        try:
            all_downloaded_files = []
            total_versions = len(versions_data)

            for i, version_info in enumerate(versions_data):
                version = version_info['version']
                task = version_info['task']
                version_code = version.get('code', 'Unknown')

                if progress.wasCanceled():
                    raise Exception("Download canceled by user")

                progress.setLabelText(
                    f"Downloading version {i + 1}/{total_versions}: {version_code}..."
                )
                progress.setValue(int((i / total_versions) * 100))
                QApplication.processEvents()

                # Download this version
                try:
                    downloaded = self.download_service.download_version(
                        version=version,
                        task_data=task,
                        progress_callback=None  # No individual progress for batch
                    )
                    all_downloaded_files.extend(downloaded)

                except Exception as e:
                    self.logger.error(
                        f"Failed to download version {version_code}: {e}"
                    )
                    # Continue with other versions

            progress.close()

            # Show summary
            if all_downloaded_files:
                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"Successfully downloaded {len(all_downloaded_files)} file(s) "
                    f"from {total_versions} version(s)."
                )

                # Emit signal
                self.files_downloaded.emit(all_downloaded_files)
            else:
                QMessageBox.warning(
                    self,
                    "No Files Downloaded",
                    "No files were downloaded. Check logs for details."
                )

        except Exception as e:
            progress.close()
            self.logger.error(f"Batch download failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Download Failed",
                f"Download was interrupted:\n{str(e)}"
            )

    # ========================================================================
    # Styling
    # ========================================================================

    def _apply_style(self):
        """Apply Jira-inspired styling to dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1D2125;
                color: #B6C2CF;
            }
            QGroupBox {
                background-color: #22272B;
                border: 1px solid #2C3338;
                border-radius: 4px;
                margin-top: 8px;
                padding: 12px;
                font-weight: bold;
                color: #B6C2CF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLabel {
                color: #B6C2CF;
                font-size: 12px;
            }
            QTreeWidget {
                background-color: #22272B;
                border: 1px solid #2C3338;
                border-radius: 4px;
                color: #B6C2CF;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #2C3338;
            }
            QTreeWidget::item:hover {
                background-color: #2C3338;
            }
            QTreeWidget::item:selected {
                background-color: #0052CC;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #2C3338;
                color: #B6C2CF;
                padding: 6px;
                border: none;
                border-right: 1px solid #1D2125;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0052CC;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0065FF;
            }
            QPushButton:pressed {
                background-color: #0747A6;
            }
            QPushButton:disabled {
                background-color: #2C3338;
                color: #505F79;
            }
        """)
