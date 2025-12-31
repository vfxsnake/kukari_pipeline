"""
Main Window for Shotgrid Manager Application

Integrates the task board UI with Shotgrid backend managers.
Uses persistent connection pattern for optimal performance.
"""

from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QStatusBar, QMenuBar,
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QCloseEvent
import logging
import os

from core.shotgrid_instance import ShotgridInstance
from core.task_manager import TaskManager
from core.asset_manager import AssetManager
from core.shot_manager import ShotManager
from core.version_manger import VersionManager
from core.published_file_manager import PublishedFileManager
from core.publishing_service import PublishingService
from ui.widgets.kanban_task_board_widget import TaskBoardWidget
from ui.widgets.shotgrid_task_data_model import ShotgridTaskDataModel
from ui.dialogs.publish_dialog import PublishDialog
from utils.logger import setup_logging


class MainWindow(QMainWindow):
    """
    Main application window for Shotgrid Manager.

    Features:
    - Task board with drag-and-drop status updates
    - Real-time integration with Shotgrid
    - Persistent connection management
    - Publishing workflow
    """

    def __init__(self):
        super().__init__()

        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)

        # Shotgrid connection and managers
        self.sg_instance = None
        self.task_manager = None
        self.asset_manager = None
        self.shot_manager = None
        self.version_manager = None
        self.published_file_manager = None
        self.publishing_service = None

        # UI state
        self.current_user_id = os.getenv('KUKARI_USER_ID')
        self.current_user = None
        self.current_project_id = None  # Will load user's projects

        # Data model for caching
        self.data_model = None

        # Setup UI
        self._setup_window()
        self._setup_menu_bar()
        self._setup_status_bar()

        # Connect to Shotgrid
        self._connect_to_shotgrid()

    def _setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("Shotgrid Manager - Kukari Animation Studio")
        self.setGeometry(100, 100, 1600, 900)

        # Set Jira-inspired dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1D2125;
            }
            QMenuBar {
                background-color: #22272B;
                color: #B6C2CF;
                padding: 4px;
                border-bottom: 1px solid #2C3338;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #0052CC;
                color: #FFFFFF;
                border-radius: 3px;
            }
            QMenuBar::item:pressed {
                background-color: #0747A6;
            }
            QStatusBar {
                background-color: #22272B;
                color: #8C9BAB;
                border-top: 1px solid #2C3338;
                padding: 4px;
            }
        """)

    def _setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # TODO: Add view options (filters, columns, etc.)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing...")

    def _connect_to_shotgrid(self):
        """
        Establish persistent connection to Shotgrid.
        Create all managers with shared connection.
        """
        try:
            self.status_bar.showMessage("Connecting to Shotgrid...")

            # Create Shotgrid instance
            self.sg_instance = ShotgridInstance()

            # Connect (persistent connection)
            self.sg_instance.connect()

            # Create all managers sharing the same connection
            self.task_manager = TaskManager(shotgun_instance=self.sg_instance)
            self.asset_manager = AssetManager(shotgun_instance=self.sg_instance)
            self.shot_manager = ShotManager(shotgun_instance=self.sg_instance)
            self.version_manager = VersionManager(shotgun_instance=self.sg_instance)
            self.published_file_manager = PublishedFileManager(shotgun_instance=self.sg_instance)

            # Create publishing service
            self.publishing_service = PublishingService(shotgun_instance=self.sg_instance)

            self.logger.info("✓ Connected to Shotgrid, all managers initialized")
            self.status_bar.showMessage("Connected to Shotgrid", 3000)

            # Now setup task board with managers available
            self._setup_task_board()

        except ValueError as e:
            self.logger.error(f"Configuration error: {e}")
            self._show_connection_error(
                "Configuration Error",
                "Missing Shotgrid credentials. Please check your environment variables:\n"
                "SG_URL, SG_SCRIPT_NAME, SG_SCRIPT_KEY"
            )

        except ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            self._show_connection_error(
                "Connection Error",
                f"Unable to connect to Shotgrid:\n{str(e)}"
            )

    def _setup_task_board(self):
        """Setup task board widget and connect signals"""
        # Create task board
        self.task_board = TaskBoardWidget()
        self.setCentralWidget(self.task_board)

        # Connect signals to slots
        self.task_board.task_status_update_requested.connect(
            self.on_task_status_update
        )
        self.task_board.publish_requested.connect(
            self.on_publish_requested
        )
        # Filter toolbar signals → handler methods (see docstrings for details)
        self.task_board.filter_toolbar.filters_changed.connect(
            self.on_filters_changed  # See line 474
        )
        self.task_board.filter_toolbar.refresh_requested.connect(
            self.refresh_data  # See line 488
        )

        # Load initial data
        self.load_projects()
        self.load_tasks()

    def load_projects(self):
        """Load available projects into filter dropdown"""
        try:
            # Query all active projects
            projects = self.sg_instance.instance.find(
                entity_type="Project",
                filters=[["is_demo", "is", False]],
                fields=["id", "name"],
                order=[{"field_name": "name", "direction": "asc"}]
            )

            self.task_board.set_projects(projects)
            self.logger.info(f"Loaded {len(projects)} projects")

        except Exception as e:
            self.logger.error(f"Failed to load projects: {e}")
            self.status_bar.showMessage(f"Error loading projects: {e}", 5000)

    def load_tasks(self, force_refresh=False):
        """
        Load tasks assigned to current user.

        Uses cached data model for fast filtering. Only queries ShotGrid
        on first load or when force_refresh=True.

        Args:
            force_refresh: Force reload from ShotGrid (default: False)
        """
        try:
            # Check if user ID is set
            if not self.current_user_id:
                self.logger.warning("KUKARI_USER_ID not set, cannot load tasks")
                self.status_bar.showMessage("Error: KUKARI_USER_ID not set", 5000)
                QMessageBox.warning(
                    self,
                    "User ID Missing",
                    "KUKARI_USER_ID environment variable is not set.\n"
                    "Please set it to your Shotgrid user ID."
                )
                return

            # Load from ShotGrid if no cache or force refresh
            if self.data_model is None or force_refresh:
                self._load_from_shotgrid()

            # Apply filters using cached data (instant!)
            self._apply_filters()

        except ValueError as e:
            self.logger.error(f"Invalid user ID: {e}")
            self.status_bar.showMessage("Error: Invalid KUKARI_USER_ID", 5000)
            QMessageBox.warning(
                self,
                "Invalid User ID",
                f"KUKARI_USER_ID must be a number.\nCurrent value: {self.current_user_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")
            self.status_bar.showMessage(f"Error loading tasks: {e}", 5000)
            QMessageBox.warning(
                self,
                "Error Loading Tasks",
                f"Failed to load tasks:\n{str(e)}"
            )

    def _load_from_shotgrid(self):
        """Load all user tasks from ShotGrid and create/refresh data model"""
        self.status_bar.showMessage("Loading from ShotGrid...")

        # Query ALL tasks for user (no filters yet - we filter locally)
        sg_filters = [
            ["task_assignees", "is", {"type": "HumanUser", "id": int(self.current_user_id)}]
        ]

        fields = [
            'id', 'content', 'sg_status_list', 'entity',
            'step', 'priority', 'task_assignees', 'due_date', 'project'
        ]

        tasks = self.task_manager.get_entities(
            filters=sg_filters,
            fields=fields,
            order=[{"field_name": "due_date", "direction": "asc"}]
        )

        # Create or refresh data model
        if self.data_model is None:
            self.data_model = ShotgridTaskDataModel(tasks)
            self.logger.info(f"Created data model with {len(tasks)} tasks")
        else:
            self.data_model.refresh(tasks)
            self.logger.info(f"Refreshed data model with {len(tasks)} tasks")

        # Update status bar with last updated time
        last_updated = self.data_model.last_updated.strftime("%H:%M:%S")
        self.status_bar.showMessage(
            f"Loaded {self.data_model.task_count} tasks (updated {last_updated})",
            3000
        )

    def _apply_filters(self):
        """Apply filters to cached data (instant - no ShotGrid query!)"""
        if self.data_model is None:
            return

        # Get current filters from UI
        filters = self.task_board.filter_toolbar.get_current_filters()

        # Apply filters using data model (LOCAL - super fast!)
        project_id = filters.get('project_id')
        entity_type = filters.get('entity_type')
        task_name = filters.get('task_name')
        search_text = filters.get('search_text')

        # Use model filtering
        if search_text:
            # Search takes precedence
            tasks = self.data_model.search_tasks(search_text)
        else:
            # Apply filters
            tasks = self.data_model.filter_tasks(
                project_id=project_id,
                entity_type=entity_type,
                task_name=task_name
            )

        # Populate board with filtered tasks
        self.task_board.populate_board(tasks)

        # Update status
        last_updated = self.data_model.last_updated.strftime("%H:%M:%S")
        self.status_bar.showMessage(
            f"Showing {len(tasks)} of {self.data_model.task_count} tasks (updated {last_updated})",
            3000
        )

    @Slot(int, str, str)
    def on_task_status_update(self, task_id, old_status, new_status):
        """
        Handle task status update when user drags task between columns.
        Uses optimistic update pattern for instant UI feedback.

        Args:
            task_id: Task ID to update
            old_status: Previous status code
            new_status: New status code
        """
        try:
            self.logger.info(f"Updating task {task_id}: {old_status} → {new_status}")

            # Map UI status codes to Shotgrid status codes
            status_map = {
                'wtg': 'wtg',  # Waiting to Start
                'ip': 'ip',    # In Progress
                'rev': 'rev',  # Pending Review
                'fin': 'fin'   # Final
            }

            sg_status = status_map.get(new_status, new_status)

            # OPTIMISTIC UPDATE: Update cache and UI immediately
            if self.data_model:
                self.data_model.update_task_status(task_id, sg_status)

            # Update UI immediately (instant feedback!)
            self.task_board.move_task_to_status(task_id, new_status)
            self.status_bar.showMessage(f"Moving task {task_id} to {self._status_name(new_status)}...")

            # Sync to ShotGrid in background
            updated_task = self.task_manager.update_entity(
                entity_id=task_id,
                data={'sg_status_list': sg_status}
            )

            if updated_task:
                self.logger.info(f"✓ Task {task_id} synced to ShotGrid successfully")
                self.status_bar.showMessage(
                    f"Task {task_id} moved to {self._status_name(new_status)}",
                    3000
                )
            else:
                raise Exception("Update returned no data")

        except Exception as e:
            self.logger.error(f"Failed to sync task {task_id} to ShotGrid: {e}")
            QMessageBox.warning(
                self,
                "Sync Failed",
                f"Failed to sync task status to ShotGrid:\n{str(e)}\n\nRefreshing to restore correct state."
            )
            # Refresh from ShotGrid to restore correct state
            self.load_tasks(force_refresh=True)

    @Slot(dict)
    def on_publish_requested(self, task_data):
        """
        Handle publish request - opens publish dialog.

        Args:
            task_data: Task dictionary from cache
        """
        self.logger.info(f"Publish requested for task {task_data.get('id')}")

        try:
            # Create and show publish dialog
            dialog = PublishDialog(
                task_data=task_data,
                publishing_service=self.publishing_service,
                version_manager=self.version_manager,
                parent=self
            )

            # Connect to publish completion signal
            dialog.publish_completed.connect(self._on_publish_completed)

            # Show dialog
            dialog.exec()

        except Exception as e:
            self.logger.error(f"Error opening publish dialog: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open publish dialog:\n{str(e)}"
            )

    @Slot(dict)
    def _on_publish_completed(self, result):
        """
        Handle successful publish completion.

        Args:
            result: Publish result dictionary from PublishingService
        """
        self.logger.info(f"Publish completed successfully")
        self.logger.info(f"Version: {result['version']['code']}")
        self.logger.info(f"Published Files: {len(result['published_files'])}")

        # Full refresh - reload all data from ShotGrid
        self.logger.info("Performing full refresh from ShotGrid...")
        self.status_bar.showMessage("Refreshing data after publish...", 2000)

        # Reload projects (in case new ones were added)
        self.load_projects()

        # Reload tasks with force refresh (clears cache, queries ShotGrid)
        self.load_tasks(force_refresh=True)

        # Update status bar
        version_code = result['version']['code']
        self.status_bar.showMessage(
            f"Published {len(result['published_files'])} file(s) as {version_code}",
            5000
        )

        self.logger.info("Full refresh completed")

    @Slot(dict)
    def on_filters_changed(self, filters):
        """
        Handle filter changes - uses cached data for instant response.

        Connected from: FilterToolbar.filters_changed signal
        Connection: line 204-205 in _connect_signals()

        Args:
            filters: Dictionary with filter values (project_id, entity_type, task_name, search_text)
        """
        self.logger.debug(f"Filters changed: {filters}")
        self._apply_filters()

    @Slot()
    def refresh_data(self):
        """
        Refresh all data from Shotgrid.

        Connected from: FilterToolbar.refresh_requested signal
        Connection: line 207-208 in _connect_signals()
        """
        self.logger.info("Refreshing data from ShotGrid...")
        self.load_tasks(force_refresh=True)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Shotgrid Manager",
            "<h2>Shotgrid Manager</h2>"
            "<p>Version 1.0.0</p>"
            "<p>Pipeline integration for Kukari Animation Studio</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Task board with drag-and-drop</li>"
            "<li>Real-time Shotgrid integration</li>"
            "<li>Publishing workflow</li>"
            "</ul>"
        )

    def _show_connection_error(self, title, message):
        """Show connection error dialog and close application"""
        QMessageBox.critical(self, title, message)
        self.close()

    def _status_name(self, status_code):
        """Convert status code to display name"""
        mapping = {
            'wtg': 'To Do',
            'rdy': 'To Do',
            'ip': 'In Progress',
            'rev': 'In Review',
            'fin': 'Done'
        }
        return mapping.get(status_code, status_code)

    def closeEvent(self, event: QCloseEvent):
        """
        Handle window close event.
        Disconnect from Shotgrid before closing.
        """
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.logger.info("Application closing...")

            # Disconnect from Shotgrid
            if self.sg_instance:
                try:
                    self.sg_instance.disconnect()
                    self.logger.info("✓ Disconnected from Shotgrid")
                except Exception as e:
                    self.logger.error(f"Error disconnecting: {e}")

            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    """Test main window standalone"""
    import sys
    from PySide6.QtWidgets import QApplication

    # Create application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())
