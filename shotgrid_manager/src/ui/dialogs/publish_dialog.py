"""
Publish Dialog for Shotgrid Manager

Allows users to:
- View task and entity information
- Add multiple files/folders to publish
- Organize files by type (editable, single delivery, multiple delivery)
- Preview what will be published in a tree view
- Execute multi-file publish to ShotGrid
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QFileDialog, QTextEdit,
    QGroupBox, QProgressDialog, QMessageBox, QApplication, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from core.publishing_service import PublishingService, PublishingError
from core.version_manger import VersionManager
from utils.zip_utility import ZipUtility


class PublishDialog(QDialog):
    """
    Dialog for publishing files to ShotGrid.

    Features:
    - Task/entity info display
    - Tree widget for organizing files
    - Support for editable, single delivery, and multiple delivery (folder) files
    - Integration with PublishingService
    - Progress tracking
    """

    # Signal emitted when publish completes successfully
    publish_completed = Signal(dict)  # Emits result dictionary

    def __init__(
        self,
        task_data: Dict,
        publishing_service: PublishingService,
        version_manager: VersionManager,
        parent=None
    ):
        """
        Initialize publish dialog.

        Args:
            task_data: Task dictionary with id, content, entity, project
            publishing_service: Publishing service instance
            version_manager: Version manager instance
            parent: Parent widget
        """
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self.task_data = task_data
        self.publishing_service = publishing_service
        self.version_manager = version_manager
        self.zip_utility = ZipUtility()

        # Extract task info
        self.task_id = task_data['id']
        self.task_name = task_data.get('content', 'Unknown Task')
        self.entity_data = task_data.get('entity', {})
        self.entity_name = self.entity_data.get('name', 'Unknown Entity') if self.entity_data else 'Unknown'
        self.project_id = task_data.get('project', {}).get('id', -1)

        # Get next version number
        self.version_number = self.version_manager.get_next_version_number_for_task(self.task_id)

        # File items storage: {tree_item: {'file_path': str, 'type': str, 'is_folder': bool}}
        self.file_items = {}

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Publish to ShotGrid")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # Task/Entity info section
        info_group = self._create_info_section()
        layout.addWidget(info_group)

        # Description field
        desc_group = QGroupBox("Version Description")
        desc_layout = QVBoxLayout(desc_group)
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("Enter version description (optional)...")
        self.description_field.setMaximumHeight(80)
        desc_layout.addWidget(self.description_field)
        layout.addWidget(desc_group)

        # Files tree section
        files_group = self._create_files_section()
        layout.addWidget(files_group)

        # Buttons
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)

    def _create_info_section(self) -> QGroupBox:
        """Create task/entity info section"""
        group = QGroupBox("Publishing To")
        layout = QVBoxLayout(group)

        # Task info
        task_label = QLabel(f"<b>Task:</b> {self.task_name}")
        layout.addWidget(task_label)

        # Entity info
        entity_label = QLabel(f"<b>Entity:</b> {self.entity_name}")
        layout.addWidget(entity_label)

        # Version info
        version_label = QLabel(f"<b>Version:</b> v{self.version_number:03d}")
        layout.addWidget(version_label)

        return group

    def _create_files_section(self) -> QGroupBox:
        """Create files tree section with add button"""
        group = QGroupBox("Files to Publish")
        layout = QVBoxLayout(group)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Version / Files", "Type", "Path"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 150)

        # Create root item (version)
        version_name = f"{self.entity_name}_{self.task_name}_v{self.version_number:03d}"
        self.root_item = QTreeWidgetItem(self.tree, [version_name, "Version", ""])
        self.root_item.setExpanded(True)

        layout.addWidget(self.tree)

        # Add files button with menu
        add_button_layout = QHBoxLayout()
        self.add_button = QPushButton("+ Add File/Folder")
        self.add_button.clicked.connect(self._show_add_menu)
        add_button_layout.addWidget(self.add_button)
        add_button_layout.addStretch()

        layout.addLayout(add_button_layout)

        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Publish button
        self.publish_button = QPushButton("Publish")
        self.publish_button.clicked.connect(self._on_publish_clicked)
        self.publish_button.setMinimumWidth(100)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(100)

        button_layout.addWidget(self.publish_button)
        button_layout.addWidget(cancel_button)

        return button_layout

    def _show_add_menu(self):
        """Show context menu for adding files"""
        menu = QMenu(self)

        # Add DCC Editable action
        editable_action = QAction("Add DCC Editable File", self)
        editable_action.triggered.connect(lambda: self._add_file("editable"))
        menu.addAction(editable_action)

        # Add Single Delivery action
        single_action = QAction("Add Single Delivery File", self)
        single_action.triggered.connect(lambda: self._add_file("single delivery"))
        menu.addAction(single_action)

        # Add Multiple Delivery Folder action
        folder_action = QAction("Add Multiple Delivery Folder", self)
        folder_action.triggered.connect(self._add_folder)
        menu.addAction(folder_action)

        # Show menu at button position
        menu.exec(self.add_button.mapToGlobal(self.add_button.rect().bottomLeft()))

    def _add_file(self, file_type: str):
        """
        Add a file to the publish tree.

        Args:
            file_type: "editable" or "single delivery"
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {file_type.title()} File",
            "",
            "All Files (*.*)"
        )

        if file_path:
            # Create tree item
            file_name = os.path.basename(file_path)
            item = QTreeWidgetItem(self.root_item, [
                file_name,
                file_type,
                file_path
            ])

            # Store file info
            self.file_items[item] = {
                'file_path': file_path,
                'type': file_type,
                'is_folder': False
            }

            self.logger.info(f"Added {file_type} file: {file_name}")

    def _add_folder(self):
        """Add a folder (multiple delivery) to the publish tree"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Multiple Delivery Folder"
        )

        if folder_path:
            # Create folder item
            folder_name = os.path.basename(folder_path)
            folder_item = QTreeWidgetItem(self.root_item, [
                folder_name + "/",
                "multiple delivery",
                folder_path
            ])

            # Store folder info
            self.file_items[folder_item] = {
                'file_path': folder_path,
                'type': "multiple delivery",
                'is_folder': True
            }

            # Recursively add folder contents for display
            self._populate_folder_tree(folder_item, folder_path)

            folder_item.setExpanded(True)
            self.logger.info(f"Added multiple delivery folder: {folder_name}")

    def _populate_folder_tree(self, parent_item: QTreeWidgetItem, folder_path: str):
        """
        Recursively populate tree with folder contents (for display only).

        Args:
            parent_item: Parent tree item
            folder_path: Path to folder
        """
        try:
            for item_name in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item_name)

                if os.path.isdir(item_path):
                    # Subfolder
                    subfolder_item = QTreeWidgetItem(parent_item, [
                        item_name + "/",
                        "",
                        item_path
                    ])
                    self._populate_folder_tree(subfolder_item, item_path)
                else:
                    # File
                    QTreeWidgetItem(parent_item, [
                        item_name,
                        "",
                        item_path
                    ])

        except Exception as e:
            self.logger.warning(f"Error reading folder {folder_path}: {e}")

    def _on_publish_clicked(self):
        """Handle publish button click"""
        # Validate we have files to publish
        if not self.file_items:
            QMessageBox.warning(
                self,
                "No Files",
                "Please add at least one file or folder to publish."
            )
            return

        # Confirm publish
        file_count = len(self.file_items)
        reply = QMessageBox.question(
            self,
            "Confirm Publish",
            f"Publish {file_count} item(s) as version v{self.version_number:03d}?\n\n"
            f"Task: {self.task_name}\n"
            f"Entity: {self.entity_name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Execute publish
        self._execute_publish()

    def _execute_publish(self):
        """Execute the publish operation"""
        try:
            # Prepare file paths and types
            files_to_publish = []

            for item, info in self.file_items.items():
                if info['is_folder']:
                    # Zip folder first
                    folder_path = info['file_path']
                    folder_name = os.path.basename(folder_path)

                    # Show progress for zipping
                    zip_msg = QMessageBox(self)
                    zip_msg.setWindowTitle("Zipping Folder")
                    zip_msg.setText(f"Compressing folder: {folder_name}")
                    zip_msg.setStandardButtons(QMessageBox.NoButton)
                    zip_msg.show()
                    QApplication.processEvents()

                    zip_path = self.zip_utility.zip_folder(folder_path)
                    zip_msg.close()

                    files_to_publish.append({
                        'file_path': zip_path,
                        'type': info['type'],
                        'is_temp': True  # Mark for cleanup
                    })
                else:
                    # Regular file
                    files_to_publish.append({
                        'file_path': info['file_path'],
                        'type': info['type'],
                        'is_temp': False
                    })

            # Create progress dialog
            progress = QProgressDialog("Publishing...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Publishing to ShotGrid")

            def update_progress(current, total, message):
                """Progress callback"""
                percentage = int((current / total) * 100)
                progress.setValue(percentage)
                progress.setLabelText(message)
                QApplication.processEvents()

                if progress.wasCanceled():
                    raise PublishingError("Publish cancelled by user")

            # Get description
            description = self.description_field.toPlainText().strip()

            # Publish using service
            file_paths = [f['file_path'] for f in files_to_publish]

            result = self.publishing_service.publish_multiple(
                task_id=self.task_id,
                file_paths=file_paths,
                description=description,
                set_task_to_review=True,
                progress_callback=update_progress
            )

            progress.close()

            # Clean up temp zip files
            for file_info in files_to_publish:
                if file_info['is_temp']:
                    try:
                        os.remove(file_info['file_path'])
                        self.logger.info(f"Cleaned up temp file: {file_info['file_path']}")
                    except:
                        pass

            # Show success message
            version_code = result['version']['code']
            pub_file_count = len(result['published_files'])

            QMessageBox.information(
                self,
                "Publish Successful",
                f"Successfully published {pub_file_count} file(s)\n\n"
                f"Version: {version_code}\n"
                f"Task: {self.task_name}\n"
                f"Entity: {self.entity_name}"
            )

            # Emit signal and close
            self.publish_completed.emit(result)
            self.accept()

        except PublishingError as e:
            QMessageBox.critical(
                self,
                "Publish Failed",
                f"Publishing failed:\n\n{str(e)}"
            )
            self.logger.error(f"Publish failed: {e}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during publish:\n\n{str(e)}"
            )
            self.logger.error(f"Unexpected error: {e}", exc_info=True)

    def _apply_style(self):
        """Apply Jira-inspired dark theme"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1D2125;
                color: #B6C2CF;
            }
            QGroupBox {
                border: 1px solid #2C3338;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
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
            }
            QTreeWidget {
                background-color: #22272B;
                color: #B6C2CF;
                border: 1px solid #2C3338;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0052CC;
            }
            QTextEdit {
                background-color: #22272B;
                color: #B6C2CF;
                border: 1px solid #2C3338;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #0052CC;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0065FF;
            }
            QPushButton:pressed {
                background-color: #0747A6;
            }
            QPushButton#add_button {
                background-color: #22272B;
                border: 1px solid #2C3338;
                color: #B6C2CF;
            }
        """)


if __name__ == "__main__":
    """Test publish dialog"""
    import sys
    from PySide6.QtWidgets import QApplication
    from core.shotgrid_instance import ShotgridInstance
    from core.task_manager import TaskManager

    # This would normally be run from main window with real data
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Mock task data (replace with real data in production)
    task_data = {
        'id': 5947,
        'content': '002_Modeling',
        'entity': {'id': 1480, 'name': 'generic_prop_1'},
        'project': {'id': 124, 'name': 'SandBox'}
    }

    # Initialize services (would come from main window)
    sg_instance = ShotgridInstance()
    sg_instance.connect()
    publish_service = PublishingService(sg_instance)
    version_manager = VersionManager(sg_instance)
    
    dialog = PublishDialog(task_data, publish_service, version_manager)
    dialog.show()
    
    sys.exit(app.exec())

    print("Publish dialog module loaded successfully")
