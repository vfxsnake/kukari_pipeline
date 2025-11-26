#!/usr/bin/env python3
"""Script to extract widgets into separate files"""

# Read original file
with open('kanban_task_board_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Extract FilterToolbar (lines 413-595 approx)
filter_toolbar_lines = lines[412:595]  # 0-indexed
filter_toolbar_content = '\n'.join(filter_toolbar_lines)

# Write FilterToolbar file
filter_toolbar_file = """# -*- coding: utf-8 -*-
\"\"\"
Filter Toolbar Widget

Toolbar for filtering tasks by project, entity type, and task type.
Provides search functionality and refresh button.
\"\"\"

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QComboBox,
                               QPushButton, QLineEdit)
from PySide6.QtCore import Signal


""" + filter_toolbar_content

with open('filter_toolbar_widget.py', 'w', encoding='utf-8') as f:
    f.write(filter_toolbar_file)

print("✓ Created filter_toolbar_widget.py")
