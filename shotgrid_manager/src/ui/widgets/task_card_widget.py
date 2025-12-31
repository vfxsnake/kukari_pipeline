# -*- coding: utf-8 -*-
"""
Task Card Widget

Individual draggable task card for Kanban board.
Displays task information in a compact, styled card format.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMenu
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QAction


class TaskCardWidget(QFrame):
    """
    Individual task card widget - draggable.

    Displays task information in a compact card format with:
    - Priority indicator
    - Task type badge
    - Entity name
    - Task name
    - Task ID

    Supports drag-and-drop to move between status columns.
    """

    # Signals
    card_clicked = Signal(dict)  # Emitted when card is double-clicked for details
    dependencies_requested = Signal(dict)  # Emitted when user requests dependency view

    def __init__(self, task_data, parent=None):
        """
        Initialize task card.

        Args:
            task_data: Dictionary containing task information
                      Required keys: 'id', 'content', 'sg_status_list'
                      Optional: 'entity', 'step', 'priority'
            parent: Parent widget
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
        """
        Convert priority number to text.

        Args:
            priority: Priority level (1=High, 2=Medium, 3=Low)

        Returns:
            Priority text with emoji
        """
        priority_map = {
            1: "HIGH",
            2: "MED",
            3: "LOW"
        }
        return priority_map.get(priority, "LOW")

    def _apply_style(self):
        """Apply Jira-inspired styling to card"""
        priority = self.task_data.get('priority', 2)

        # Jira-style color scheme
        style = """
            TaskCardWidget {
                background-color: #2C3338;
                border: 1px solid %s;
                border-radius: 4px;
                margin: 4px;
                padding: 2px;
            }
            TaskCardWidget:hover {
                background-color: #343B41;
                border-color: #4a9eff;
            }
            QLabel[priority] {
                color: #B6C2CF;
                font-weight: bold;
                font-size: 10px;
            }
            QLabel[task-name="true"] {
                font-weight: bold;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLabel[entity="true"] {
                color: #9FADBC;
                font-size: 10px;
            }
            QLabel[task-id="true"] {
                color: #8C9BAB;
                font-size: 9px;
            }
            QLabel[task-type="true"] {
                background-color: #216E4E;
                color: #FFFFFF;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
        """

        # Priority-based border color (subtle, Jira-style)
        border_color = {
            1: "#E34935",  # High - Red
            2: "#F5CD47",  # Medium - Yellow
            3: "#505F79"   # Low - Blue-gray
        }.get(priority, "#505F79")

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

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu(self)

        # View Details action (same as double-click)
        details_action = QAction("View Details", self)
        details_action.triggered.connect(lambda: self.card_clicked.emit(self.task_data))
        menu.addAction(details_action)

        menu.addSeparator()

        # View Dependencies action
        dependencies_action = QAction("View Dependencies", self)
        dependencies_action.triggered.connect(
            lambda: self.dependencies_requested.emit(self.task_data)
        )
        menu.addAction(dependencies_action)

        # Show menu at cursor position
        menu.exec_(event.globalPos())
