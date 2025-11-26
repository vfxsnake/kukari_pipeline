# -*- coding: utf-8 -*-
"""
Filter Toolbar Widget

Toolbar for filtering tasks by project, entity type, and task type.
Provides search functionality and refresh button.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QComboBox,
                               QPushButton, QLineEdit)
from PySide6.QtCore import Signal


class FilterToolbar(QWidget):
    """
    Toolbar for filtering tasks
    Provides project, entity type, and task type filters
    """
    
    # Signal emitted when filters change
    filters_changed = Signal(dict)  # Emits filter dictionary
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup toolbar layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Project filter
        layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setPlaceholderText("Select Project")
        layout.addWidget(self.project_combo)
        
        layout.addSpacing(20)
        
        # Entity type filter
        layout.addWidget(QLabel("Entity Type:"))
        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItems(["All", "Shot", "Asset"])
        layout.addWidget(self.entity_type_combo)
        
        layout.addSpacing(20)
        
        # Task type filter
        layout.addWidget(QLabel("Task Type:"))
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItem("All")
        # Common task types - can be populated dynamically
        task_types = ["Animation", "Modeling", "Rigging", "Texturing", 
                     "Lighting", "Layout", "FX", "Compositing"]
        self.task_type_combo.addItems(task_types)
        layout.addWidget(self.task_type_combo)
        
        layout.addSpacing(20)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tasks...")
        self.search_input.setMaximumWidth(200)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
        self._apply_style()
        
    def _apply_style(self):
        """Apply toolbar styling - Jira-inspired"""
        style = """
            FilterToolbar {
                background-color: #22272B;
                border-bottom: 1px solid #2C3338;
                padding: 4px;
            }
            QLabel {
                color: #B6C2CF;
                font-weight: 500;
                font-size: 12px;
            }
            QComboBox, QLineEdit {
                padding: 6px 8px;
                border: 1px solid #38414A;
                border-radius: 3px;
                background-color: #2C3338;
                color: #B6C2CF;
                selection-background-color: #0052CC;
            }
            QComboBox:hover, QLineEdit:hover {
                background-color: #343B41;
                border-color: #505F79;
            }
            QComboBox:focus, QLineEdit:focus {
                border-color: #0052CC;
                background-color: #2C3338;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #2C3338;
                color: #B6C2CF;
                selection-background-color: #0052CC;
                selection-color: #FFFFFF;
                border: 1px solid #38414A;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #343B41;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0052CC;
                color: #FFFFFF;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #0052CC;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0065FF;
            }
            QPushButton:pressed {
                background-color: #0747A6;
            }
        """
        self.setStyleSheet(style)
    
    def _connect_signals(self):
        """Connect filter change signals"""
        self.project_combo.currentIndexChanged.connect(self._emit_filters)
        self.entity_type_combo.currentTextChanged.connect(self._emit_filters)
        self.task_type_combo.currentTextChanged.connect(self._emit_filters)
        self.search_input.textChanged.connect(self._emit_filters)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        
    def _emit_filters(self):
        """Emit current filter state"""
        filters = self.get_current_filters()
        self.filters_changed.emit(filters)
    
    def get_current_filters(self):
        """
        Get current filter values
        
        Returns:
            dict: Filter values
        """
        project_data = self.project_combo.currentData()
        entity_type = self.entity_type_combo.currentText()
        task_type = self.task_type_combo.currentText()
        search_text = self.search_input.text().strip()
        
        return {
            'project_id': project_data if project_data else None,
            'entity_type': entity_type if entity_type != "All" else None,
            'task_type': task_type if task_type != "All" else None,
            'search_text': search_text if search_text else None
        }
    
    def set_projects(self, projects):
        """
        Populate project dropdown
        
        Args:
            projects: List of project dicts [{'id': 1, 'name': 'Project1'}, ...]
        """
        self.project_combo.clear()
        for project in projects:
            self.project_combo.addItem(project['name'], project['id'])


# ============================================================================
# src/ui/widgets/task_board_widget.py
# ============================================================================
