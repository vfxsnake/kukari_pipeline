"""
Task Board UI Implementation for Shotgrid Publisher
UI components only - assumes task data retrieval is already implemented
"""

# ============================================================================
# src/ui/widgets/task_card_widget.py
# ============================================================================

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter


class TaskCardWidget(QFrame):
    """
    Individual task card widget - draggable
    Displays task information in a compact card format
    """
    
    # Signal emitted when card is clicked for details
    card_clicked = Signal(dict)  # Emits task data
    
    def __init__(self, task_data, parent=None):
        """
        Args:
            task_data: Dictionary containing task information
                      {'id', 'content', 'entity', 'step', 'sg_status_list', 'priority', ...}
        """
        super().__init__(parent)
        
        self.task_data = task_data
        self.drag_start_position = None
        
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        """Setup card layout and widgets"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Top row: Priority indicator and task type
        top_layout = QHBoxLayout()
        
        # Priority indicator
        priority = self.task_data.get('priority', 2)
        priority_text = self._get_priority_text(priority)
        self.priority_label = QLabel(priority_text)
        self.priority_label.setProperty('priority', priority)
        top_layout.addWidget(self.priority_label)
        
        # Task type/step
        step = self.task_data.get('step', {})
        if step:
            step_name = step.get('name', 'Unknown')
            self.type_label = QLabel(f"[{step_name}]")
            self.type_label.setProperty('task-type', True)
            top_layout.addWidget(self.type_label)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Entity name (Shot/Asset code)
        entity = self.task_data.get('entity', {})
        if entity:
            entity_name = entity.get('name', 'Unknown')
            entity_type = entity.get('type', 'Entity')
            self.entity_label = QLabel(f"{entity_type}: {entity_name}")
            self.entity_label.setProperty('entity', True)
            layout.addWidget(self.entity_label)
        
        # Task name
        task_name = self.task_data.get('content', 'Unnamed Task')
        self.task_label = QLabel(task_name)
        self.task_label.setWordWrap(True)
        self.task_label.setProperty('task-name', True)
        layout.addWidget(self.task_label)
        
        # Task ID (small, for reference)
        task_id = self.task_data.get('id', 0)
        self.id_label = QLabel(f"#{task_id}")
        self.id_label.setProperty('task-id', True)
        layout.addWidget(self.id_label)
        
        self.setLayout(layout)
        
    def _get_priority_text(self, priority):
        """Convert priority number to text"""
        priority_map = {
            1: "🔴 HIGH",
            2: "🟡 MED",
            3: "⚪ LOW"
        }
        return priority_map.get(priority, "⚪ LOW")
    
    def _apply_style(self):
        """Apply QSS styling to card"""
        priority = self.task_data.get('priority', 2)
        
        # Base style
        style = """
            TaskCardWidget {
                background-color: #2b2b2b;
                border: 2px solid %s;
                border-radius: 6px;
                margin: 4px;
            }
            TaskCardWidget:hover {
                background-color: #3a3a3a;
                border-color: #4a9eff;
            }
            QLabel[task-name="true"] {
                font-weight: bold;
                color: #ffffff;
            }
            QLabel[entity="true"] {
                color: #aaaaaa;
                font-size: 11px;
            }
            QLabel[task-id="true"] {
                color: #666666;
                font-size: 10px;
            }
            QLabel[task-type="true"] {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
            }
        """
        
        # Priority-based border color
        border_color = {
            1: "#ff4444",  # High - Red
            2: "#ffaa00",  # Medium - Orange
            3: "#888888"   # Low - Gray
        }.get(priority, "#888888")
        
        self.setStyleSheet(style % border_color)
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to start drag operation"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if not self.drag_start_position:
            return
        
        # Check if moved enough to start drag
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Store task ID and current status in mime data
        task_id = str(self.task_data.get('id'))
        current_status = self.task_data.get('sg_status_list', 'wtg')
        
        mime_data.setText(f"{task_id}|{current_status}")
        drag.setMimeData(mime_data)
        
        # Create drag pixmap (visual representation while dragging)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        
        # Make it semi-transparent
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), Qt.GlobalColor.gray)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute drag
        drag.exec_(Qt.MoveAction)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to view task details"""
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.task_data)
        super().mouseDoubleClickEvent(event)


# ============================================================================
# src/ui/widgets/task_column_widget.py
# ============================================================================

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                               QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal


class TaskColumnWidget(QFrame):
    """
    Column widget for a specific task status
    Contains multiple task cards and accepts drops
    """
    
    # Signal emitted when a task is dropped into this column
    task_dropped = Signal(int, str, str)  # task_id, old_status, new_status
    
    def __init__(self, status_name, status_code, parent=None):
        """
        Args:
            status_name: Display name (e.g., "To Do", "In Progress")
            status_code: Shotgrid status code (e.g., "wtg", "ip")
        """
        super().__init__(parent)
        
        self.status_name = status_name
        self.status_code = status_code
        self.task_cards = []
        
        self.setAcceptDrops(True)
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        """Setup column layout"""
        self.setFrameShape(QFrame.StyledPanel)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)
        
        # Header with status name and count
        header_layout = QVBoxLayout()
        
        self.title_label = QLabel(self.status_name)
        self.title_label.setProperty('column-title', True)
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)
        
        self.count_label = QLabel("0")
        self.count_label.setProperty('task-count', True)
        self.count_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.count_label)
        
        main_layout.addLayout(header_layout)
        
        # Scrollable area for task cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(4)
        self.cards_layout.addStretch()
        
        scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def _apply_style(self):
        """Apply column styling"""
        style = """
            TaskColumnWidget {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                min-width: 280px;
                max-width: 320px;
            }
            QLabel[column-title="true"] {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 8px;
            }
            QLabel[task-count="true"] {
                font-size: 14px;
                color: #888888;
                padding: 4px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """
        self.setStyleSheet(style)
    
    def add_task_card(self, task_data):
        """
        Add a task card to this column
        
        Args:
            task_data: Task dictionary
        """
        card = TaskCardWidget(task_data)
        self.task_cards.append(card)
        
        # Insert before stretch
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        
        self._update_count()
    
    def remove_task_card(self, task_id):
        """
        Remove a task card by ID
        
        Args:
            task_id: Task ID to remove
        """
        for card in self.task_cards:
            if card.task_data.get('id') == task_id:
                self.cards_layout.removeWidget(card)
                self.task_cards.remove(card)
                card.deleteLater()
                break
        
        self._update_count()
    
    def clear_cards(self):
        """Remove all task cards"""
        for card in self.task_cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        
        self.task_cards.clear()
        self._update_count()
    
    def _update_count(self):
        """Update task count label"""
        count = len(self.task_cards)
        self.count_label.setText(str(count))
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasText():
            # Check if it's a valid task drag
            data = event.mimeData().text()
            if '|' in data:
                event.acceptProposedAction()
                self.setProperty('drop-active', True)
                self.style().unpolish(self)
                self.style().polish(self)
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setProperty('drop-active', False)
        self.style().unpolish(self)
        self.style().polish(self)
    
    def dropEvent(self, event):
        """Handle drop event"""
        self.setProperty('drop-active', False)
        self.style().unpolish(self)
        self.style().polish(self)
        
        if event.mimeData().hasText():
            data = event.mimeData().text()
            
            if '|' in data:
                task_id_str, old_status = data.split('|')
                task_id = int(task_id_str)
                
                # Don't emit if dropping in same column
                if old_status != self.status_code:
                    self.task_dropped.emit(task_id, old_status, self.status_code)
                    event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()


# ============================================================================
# src/ui/widgets/filter_toolbar.py
# ============================================================================

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
        """Apply toolbar styling"""
        style = """
            FilterToolbar {
                background-color: #2b2b2b;
                border-bottom: 2px solid #3a3a3a;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QComboBox, QLineEdit {
                padding: 6px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QComboBox:hover, QLineEdit:hover {
                border-color: #4a9eff;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #4a9eff;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5aa9ff;
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

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Signal, Slot


class TaskBoardWidget(QWidget):
    """
    Main task board widget containing columns and filter toolbar
    """
    
    # Signals
    task_status_update_requested = Signal(int, str, str)  # task_id, old_status, new_status
    publish_requested = Signal(dict)  # task_data
    
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
        """Apply board styling"""
        style = """
            TaskBoardWidget {
                background-color: #1a1a1a;
            }
        """
        self.setStyleSheet(style)
    
    def _connect_signals(self):
        """Connect all signals"""
        # Filter changes
        self.filter_toolbar.filters_changed.connect(self.on_filters_changed)
        self.filter_toolbar.refresh_requested.connect(self.refresh_board)
        
        # Drag and drop
        for column in self.columns.values():
            column.task_dropped.connect(self.on_task_dropped)
    
    @Slot(int, str, str)
    def on_task_dropped(self, task_id, old_status, new_status):
        """
        Handle task drop event
        
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
        Handle filter changes
        
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
        Populate board with tasks
        
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
        Move task card from one column to another
        
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


# ============================================================================
# Test/Demo Application
# ============================================================================

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel


class MockPublishDialog(QDialog):
    """Mock publish dialog for testing"""
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setWindowTitle("Publish Dialog")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Show task info
        info_label = QLabel(
            f"Publishing for:\n"
            f"Task: {task_data.get('content', 'Unknown')}\n"
            f"Entity: {task_data.get('entity', {}).get('name', 'Unknown')}\n"
            f"Type: {task_data.get('step', {}).get('name', 'Unknown')}"
        )
        layout.addWidget(info_label)
        
        # Buttons
        publish_btn = QPushButton("Publish")
        publish_btn.clicked.connect(self.accept)
        layout.addWidget(publish_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)


class TestMainWindow(QMainWindow):
    """Test window with mock data"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Shotgrid Task Board - Test Mode")
        self.setGeometry(100, 100, 1400, 800)
        
        # Mock data
        self.mock_tasks = self._create_mock_tasks()
        self.mock_projects = self._create_mock_projects()
        
        self.setup_task_board()
        
    def _create_mock_projects(self):
        """Create mock project data"""
        return [
            {'id': 1, 'name': 'Beyond Gravity'},
            {'id': 2, 'name': 'Space Odyssey'},
            {'id': 3, 'name': 'Lunar Base'},
        ]
    
    def _create_mock_tasks(self):
        """Create mock task data for testing"""
        tasks = [
            # To Do tasks
            {
                'id': 1,
                'content': 'Character rigging',
                'entity': {'name': 'char_hero', 'type': 'Asset'},
                'step': {'name': 'Rigging', 'code': 'Rig'},
                'sg_status_list': 'wtg',
                'priority': 1,
            },
            {
                'id': 2,
                'content': 'Environment modeling',
                'entity': {'name': 'env_forest', 'type': 'Asset'},
                'step': {'name': 'Modeling', 'code': 'Mdl'},
                'sg_status_list': 'wtg',
                'priority': 2,
            },
            {
                'id': 3,
                'content': 'Prop texturing',
                'entity': {'name': 'prop_table', 'type': 'Asset'},
                'step': {'name': 'Texturing', 'code': 'Tex'},
                'sg_status_list': 'rdy',
                'priority': 3,
            },
            
            # In Progress tasks
            {
                'id': 4,
                'content': 'Character animation',
                'entity': {'name': 'shot_010', 'type': 'Shot'},
                'step': {'name': 'Animation', 'code': 'Anim'},
                'sg_status_list': 'ip',
                'priority': 1,
            },
            {
                'id': 5,
                'content': 'Camera layout',
                'entity': {'name': 'shot_020', 'type': 'Shot'},
                'step': {'name': 'Layout', 'code': 'Lay'},
                'sg_status_list': 'ip',
                'priority': 2,
            },
            {
                'id': 6,
                'content': 'FX simulation',
                'entity': {'name': 'shot_030', 'type': 'Shot'},
                'step': {'name': 'FX', 'code': 'FX'},
                'sg_status_list': 'ip',
                'priority': 1,
            },
            
            # In Review tasks
            {
                'id': 7,
                'content': 'Lighting setup',
                'entity': {'name': 'shot_040', 'type': 'Shot'},
                'step': {'name': 'Lighting', 'code': 'Lgt'},
                'sg_status_list': 'rev',
                'priority': 2,
            },
            {
                'id': 8,
                'content': 'Compositing',
                'entity': {'name': 'shot_050', 'type': 'Shot'},
                'step': {'name': 'Compositing', 'code': 'Comp'},
                'sg_status_list': 'rev',
                'priority': 1,
            },
            
            # Done tasks
            {
                'id': 9,
                'content': 'Concept art',
                'entity': {'name': 'char_hero', 'type': 'Asset'},
                'step': {'name': 'Concept', 'code': 'Cpt'},
                'sg_status_list': 'fin',
                'priority': 2,
            },
            {
                'id': 10,
                'content': 'Storyboard',
                'entity': {'name': 'seq_010', 'type': 'Sequence'},
                'step': {'name': 'Story', 'code': 'Stry'},
                'sg_status_list': 'fin',
                'priority': 3,
            },
        ]
        
        return tasks
    
    def setup_task_board(self):
        """Setup task board"""
        # Create task board
        self.task_board = TaskBoardWidget()
        self.setCentralWidget(self.task_board)
        
        # Connect signals
        self.task_board.task_status_update_requested.connect(
            self.on_task_status_update
        )
        self.task_board.publish_requested.connect(
            self.on_publish_requested
        )
        self.task_board.filter_toolbar.filters_changed.connect(
            self.on_filters_changed
        )
        self.task_board.filter_toolbar.refresh_requested.connect(
            self.load_tasks
        )
        
        # Load initial data
        self.load_projects()
        self.load_tasks()
    
    def load_projects(self):
        """Load mock projects"""
        self.task_board.set_projects(self.mock_projects)
    
    def load_tasks(self):
        """Load tasks with current filters"""
        # Get current filters
        filters = self.task_board.filter_toolbar.get_current_filters()
        
        # Filter tasks
        filtered_tasks = self.filter_mock_tasks(filters)
        
        # Populate board
        self.task_board.populate_board(filtered_tasks)
        
        print(f"Loaded {len(filtered_tasks)} tasks with filters: {filters}")
    
    def filter_mock_tasks(self, filters):
        """Filter mock tasks based on filters"""
        filtered = self.mock_tasks.copy()
        
        # Filter by entity type
        if filters.get('entity_type'):
            filtered = [
                t for t in filtered 
                if t.get('entity', {}).get('type') == filters['entity_type']
            ]
        
        # Filter by task type
        if filters.get('task_type'):
            filtered = [
                t for t in filtered 
                if t.get('step', {}).get('name') == filters['task_type']
            ]
        
        # Filter by search text
        if filters.get('search_text'):
            search_lower = filters['search_text'].lower()
            filtered = [
                t for t in filtered 
                if search_lower in t.get('content', '').lower()
            ]
        
        return filtered
    
    def on_filters_changed(self, filters):
        """Handle filter changes"""
        print(f"Filters changed: {filters}")
        self.load_tasks()
    
    def on_task_status_update(self, task_id, old_status, new_status):
        """Handle task status update"""
        print(f"Status update: Task #{task_id} from {old_status} to {new_status}")
        
        # Simulate successful update
        # In real app, this would call Shotgrid API
        success = True
        
        if success:
            # Update mock data
            for task in self.mock_tasks:
                if task['id'] == task_id:
                    task['sg_status_list'] = new_status
                    break
            
            # Move card visually
            self.task_board.move_task_to_status(task_id, new_status)
            
            # Show feedback
            self.statusBar().showMessage(
                f"Task #{task_id} moved to {self._status_name(new_status)}", 
                3000
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to update task status")
    
    def on_publish_requested(self, task_data):
        """Handle publish request"""
        print(f"Publish requested for task: {task_data.get('content')}")
        
        # Show mock publish dialog
        dialog = MockPublishDialog(task_data, self)
        
        if dialog.exec():
            # Publish successful - move task to In Review
            task_id = task_data['id']
            
            # Simulate successful publish
            print(f"Publishing task #{task_id}...")
            
            # Update status
            self.on_task_status_update(task_id, task_data['sg_status_list'], 'rev')
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Task #{task_id} published successfully!\nMoved to In Review."
            )
        else:
            print("Publish cancelled")
            self.statusBar().showMessage("Publish cancelled", 3000)
    
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


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TestMainWindow()
    window.show()
    
    print("=" * 60)
    print("Task Board Test Application")
    print("=" * 60)
    print("\nFeatures to test:")
    print("- Drag tasks between columns (To Do → In Progress → In Review → Done)")
    print("- Drop task in 'In Review' triggers publish dialog")
    print("- Filter by Entity Type (All/Shot/Asset)")
    print("- Filter by Task Type (All/Animation/Modeling/etc.)")
    print("- Search tasks by name")
    print("- Click Refresh to reload")
    print("\nConsole output will show events...")
    print("=" * 60)
    print()
    
    # Run application
    sys.exit(app.exec())