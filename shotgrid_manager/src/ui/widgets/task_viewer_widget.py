import sys
from typing import List, Set
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QPushButton,
    QFormLayout,
    QLabel,
    QAbstractItemView
)

from PySide6.QtCore import Qt
from core.task_manager import TaskManager


class ShotgunTaskDataModel():
    def __init__(self, shotgun_task_data:List[dict]):
        self._data = shotgun_task_data
        print("_data type is: ",type(self._data))

    def get_projects(self)->Set[dict]:
        return {(task.get('project',{}).get("name"), task.get('project',{}).get("id")) for task in self._data}
        

    def get_project_tasks(self, project_id:int)->List[dict]:
        return [task for task in self._data if task.get("project", {}).get("id", -1)==project_id]
    
        

class TaskViewerWidget(QWidget):
    """
    A widget to display and filter ShotGrid tasks.

    This widget follows a Model-View-Controller (MVC) like pattern where:
    - Model: The `TaskManager` instance, which handles data logic.
    - View: The Qt widgets themselves (table, combo box).
    - Controller: The methods within this class that handle user input
                  and update the view (`on_project_changed`, `_populate_tasks`).
    """
    HEADER_LABELS = ["Entity", "Task", "Due Date", "Priority", "status"]

    def __init__(self, shotgun_data_model, parent=None):
        """
        Initializes the TaskViewerWidget.

        Args:
            shotgun_data_model (ShotgunTaskDataModel): An instance of the TaskManager class
                                        that will provide the task data.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        if not isinstance(shotgun_data_model, ShotgunTaskDataModel):
            raise TypeError("shotgun_data_model must be an instance of ShotgunTaskDataModel")

        self.shotgun_data_model = shotgun_data_model
        
        self.setWindowTitle("Task Viewer")
        self.setGeometry(100, 100, 800, 600)

        self._init_ui()
        self._connect_signals()
        self._populate_projects()
        self._populate_tasks()

    def _init_ui(self):
        """Initializes the UI components and layout."""
        main_layout = QVBoxLayout(self)

        # --- Filter Controls ---
        filter_group = QGroupBox("Filter")
        form_layout = QFormLayout()
        self.project_combo = QComboBox()
        form_layout.addRow(QLabel("Project:"), self.project_combo)
        filter_group.setLayout(form_layout)

        # --- Task Table ---
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(len(self.HEADER_LABELS))
        self.task_table.setHorizontalHeaderLabels(self.HEADER_LABELS)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        
        # Set header resize modes
        horizontal_header = self.task_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # --- Publish Placeholder ---
        publish_group = QGroupBox("Publish")
        publish_layout = QVBoxLayout()
        publish_button = QPushButton("Publish New Version (Not Implemented)")
        publish_button.setEnabled(False)
        publish_layout.addWidget(publish_button)
        publish_group.setLayout(publish_layout)
        publish_group.setFixedHeight(100)

        # --- Main Layout ---
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.task_table)
        main_layout.addWidget(publish_group)

    def _connect_signals(self):
        """Connects widget signals to corresponding slots."""
        self.project_combo.currentTextChanged.connect(self.on_project_changed)

    def _populate_projects(self):
        """Populates the project combo box with project names."""
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        
        projects = self.shotgun_data_model.get_projects()
        self.project_combo.addItem(" ", userData=-1)  # empty value
        for project in projects:
            self.project_combo.addItem(project[0], userData=project[1])
        self.project_combo.blockSignals(False)

    def _populate_tasks(self):
        """Populates the table with tasks based on the current filter."""
        selected_project_id = self.project_combo.currentData()
        if selected_project_id == -1:
            self.task_table.setRowCount(0)
            self.task_table.setSortingEnabled(False)
            return 
        
        tasks = self.shotgun_data_model.get_project_tasks(project_id=selected_project_id)

        self.task_table.setRowCount(0)
        self.task_table.setSortingEnabled(False)

        for row, task_data in enumerate(tasks):
            self.task_table.insertRow(row)

            # Task Name (content)
            entity = task_data.get('entity', {}).get('name')
            self.task_table.setItem(row, 0, QTableWidgetItem(entity))
            
            task_name = task_data.get("content", "N/A")
            item = QTableWidgetItem(task_name)
            item.setData(Qt.UserRole, task_data.get("id"))
            self.task_table.setItem(row, 1, item)

            # Due Date
            due_date = task_data.get("due_date", "N/A")
            self.task_table.setItem(row, 2, QTableWidgetItem(due_date))

            # Priority
            priority = task_data.get("sg_priority_1", "N/A")
            self.task_table.setItem(row, 3, QTableWidgetItem(priority))

            # Priority
            status = task_data.get("sg_status_list", "N/A")
            self.task_table.setItem(row, 4, QTableWidgetItem(status))
        
        self.task_table.setSortingEnabled(True)

    def on_project_changed(self, project_name: str):
        """
        Slot that is called when the selected project changes.
        Updates the task list in the table.
        """
        self._populate_tasks()


# To make the widget runnable for testing purposes
if __name__ == '__main__':
    # This block will only execute when the script is run directly
    # and not when it's imported into another application like Maya or Houdini.
    from core.shotgrid_instance import ShotgridInstance

    app = QApplication(sys.argv)
    
    # 1. Create the Model/Manager
    
    flow = ShotgridInstance()

    task_manager = TaskManager(flow)
    task_manager.connect()
    data = task_manager.get_tasks(19)
    data_model = ShotgunTaskDataModel(data)

    # 2. Create the View/Widget and inject the model
    viewer_widget = TaskViewerWidget(shotgun_data_model=data_model)

    # 3. Show the widget and run the application
    viewer_widget.show()
    
    sys.exit(app.exec())
