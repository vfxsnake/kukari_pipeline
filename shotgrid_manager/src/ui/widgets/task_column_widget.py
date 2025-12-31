# -*- coding: utf-8 -*-
"""
Task Column Widget

Column for holding task cards of a specific status.
Supports drag-and-drop to move tasks between columns.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QScrollArea)
from PySide6.QtCore import Qt, Signal

from .task_card_widget import TaskCardWidget


class TaskColumnWidget(QFrame):
    """
    Column widget for a specific task status.

    Contains multiple task cards and accepts drops for drag-and-drop
    task status updates.
    """

    # Signals
    task_dropped = Signal(int, str, str)  # task_id, old_status, new_status
    dependencies_requested = Signal(dict)  # task_data

    def __init__(self, status_name, status_code, parent=None):
        """
        Initialize column.

        Args:
            status_name: Display name (e.g., "To Do", "In Progress")
            status_code: Shotgrid status code (e.g., "wtg", "ip")
            parent: Parent widget
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
        """Apply Jira-inspired column styling"""
        style = """
            TaskColumnWidget {
                background-color: #22272B;
                border: none;
                border-radius: 4px;
                min-width: 280px;
                max-width: 320px;
            }
            QLabel[column-title="true"] {
                font-size: 14px;
                font-weight: 600;
                color: #B6C2CF;
                padding: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QLabel[task-count="true"] {
                font-size: 12px;
                color: #8C9BAB;
                padding: 4px;
            }
            QScrollArea {
                border: none;
                background-color: #22272B;
            }
            QWidget {
                background-color: #22272B;
            }
        """
        self.setStyleSheet(style)

    def add_task_card(self, task_data):
        """
        Add a task card to this column.

        Args:
            task_data: Task dictionary
        """
        card = TaskCardWidget(task_data)
        self.task_cards.append(card)

        # Connect card signals
        card.dependencies_requested.connect(self.dependencies_requested.emit)

        # Insert before stretch
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self._update_count()

    def remove_task_card(self, task_id):
        """
        Remove a task card by ID.

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
