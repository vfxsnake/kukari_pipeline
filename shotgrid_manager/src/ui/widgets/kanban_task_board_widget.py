# -*- coding: utf-8 -*-
"""
Task Board Widget

Main Kanban-style task board widget that assembles all components.
Integrates task cards, columns, and filter toolbar into a complete board.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Signal, Slot

from .task_card_widget import TaskCardWidget
from .task_column_widget import TaskColumnWidget
from .filter_toolbar_widget import FilterToolbar


class TaskBoardWidget(QWidget):
    """
    Main task board widget containing columns and filter toolbar.

    Provides a Kanban-style interface for managing tasks with drag-and-drop
    status updates.
    """

    # Signals
    task_status_update_requested = Signal(int, str, str)  # task_id, old_status, new_status
    publish_requested = Signal(dict)  # task_data
    dependencies_requested = Signal(dict)  # task_data

    def __init__(self, parent=None):
        super().__init__(parent)

        # Status columns configuration
        self.status_columns = [
            ('To Do', 'wtg'),
            ('In Progress', 'ip'),
            ('In Review', 'rev'),
            ('Done', 'fin')
        ]

        self.columns = {}
        self.current_tasks = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup main board layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Filter toolbar at top
        self.filter_toolbar = FilterToolbar()
        main_layout.addWidget(self.filter_toolbar)

        # Columns container
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(12, 12, 12, 12)
        columns_layout.setSpacing(12)

        # Create status columns
        for status_name, status_code in self.status_columns:
            column = TaskColumnWidget(status_name, status_code)
            self.columns[status_code] = column
            columns_layout.addWidget(column)

        main_layout.addLayout(columns_layout)

        self.setLayout(main_layout)
        self._apply_style()

    def _apply_style(self):
        """Apply Jira-inspired board styling"""
        style = """
            TaskBoardWidget {
                background-color: #1D2125;
            }
        """
        self.setStyleSheet(style)

    def _connect_signals(self):
        """Connect all signals"""
        # Filter changes
        self.filter_toolbar.filters_changed.connect(self.on_filters_changed)
        self.filter_toolbar.refresh_requested.connect(self.refresh_board)

        # Connect column signals
        for column in self.columns.values():
            # Drag and drop
            column.task_dropped.connect(self.on_task_dropped)
            # Dependencies requested
            column.dependencies_requested.connect(self.dependencies_requested.emit)

    @Slot(int, str, str)
    def on_task_dropped(self, task_id, old_status, new_status):
        """
        Handle task drop event.

        Args:
            task_id: Task ID
            old_status: Previous status code
            new_status: New status code
        """
        # Get task data
        task_data = self._find_task_by_id(task_id)
        if not task_data:
            return

        # Special handling for "In Review" status - show publish dialog
        if new_status == 'rev':  # In Review
            self.publish_requested.emit(task_data)
            # Note: Actual move happens after publish dialog completes successfully
        else:
            # For other status changes, emit update request
            self.task_status_update_requested.emit(task_id, old_status, new_status)

    @Slot(dict)
    def on_filters_changed(self, filters):
        """
        Handle filter changes.

        Args:
            filters: Filter dictionary
        """
        # Filter will be handled by parent widget/window
        # that has access to task data source
        pass

    @Slot()
    def refresh_board(self):
        """Refresh board - handled by parent"""
        pass

    def populate_board(self, tasks):
        """
        Populate board with tasks.

        Args:
            tasks: List of task dictionaries
        """
        # Clear existing cards
        for column in self.columns.values():
            column.clear_cards()

        self.current_tasks = tasks

        # Status mapping from Shotgrid to UI
        status_map = {
            'wtg': 'wtg',   # Waiting to Start -> To Do
            'rdy': 'wtg',   # Ready to Start -> To Do
            'ip': 'ip',     # In Progress -> In Progress
            'rev': 'rev',   # Pending Review -> In Review
            'fin': 'fin',   # Final -> Done
            'omt': 'fin',   # Omitted -> Done
        }

        # Add tasks to appropriate columns
        for task in tasks:
            sg_status = task.get('sg_status_list', 'wtg')
            ui_status = status_map.get(sg_status, 'wtg')

            if ui_status in self.columns:
                self.columns[ui_status].add_task_card(task)

    def move_task_to_status(self, task_id, new_status_code):
        """
        Move task card from one column to another.

        Args:
            task_id: Task ID
            new_status_code: New status code (wtg, ip, rev, fin)
        """
        # Find task data
        task_data = self._find_task_by_id(task_id)
        if not task_data:
            return

        old_status = task_data.get('sg_status_list', 'wtg')

        # Status mapping
        status_map = {
            'wtg': 'wtg', 'rdy': 'wtg',
            'ip': 'ip',
            'rev': 'rev',
            'fin': 'fin', 'omt': 'fin'
        }

        old_ui_status = status_map.get(old_status, 'wtg')

        # Remove from old column
        if old_ui_status in self.columns:
            self.columns[old_ui_status].remove_task_card(task_id)

        # Update task data
        task_data['sg_status_list'] = new_status_code

        # Add to new column
        if new_status_code in self.columns:
            self.columns[new_status_code].add_task_card(task_data)

    def _find_task_by_id(self, task_id):
        """Find task in current tasks list"""
        for task in self.current_tasks:
            if task.get('id') == task_id:
                return task
        return None

    def set_projects(self, projects):
        """Set available projects in filter"""
        self.filter_toolbar.set_projects(projects)
