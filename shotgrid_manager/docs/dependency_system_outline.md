# Dependency Resolution System - Implementation Outline

## User Interaction Flow

```
Task Card (Right-Click) → "View Dependencies" → Dependencies Dialog
                                                  ↓
                                          Tree View Display:
                                          ├─ Upstream Tasks
                                          │  └─ Art - v003
                                          │     ├─ concept_sketch.jpg
                                          │     └─ reference.zip
                                          └─ Asset Dependencies
                                             └─ Character_Cianlu - Rig v005
                                                ├─ cianlu_rig.ma
                                                └─ controls.json
```

---

## Pipeline Rules

### Assets
- **Art** → No dependencies
- **Modeling** → Art (latest version)
- **Rig** → Modeling (latest version)
- **Surfacing** → Modeling (latest version)

### Shots
- **Layout** → All shot assets (Rigs preferred, fallback to Models)
- **Animation** → Layout + All shot assets (Rigs preferred)
- **Lighting** → Animation (fallback: Layout) + All shot assets
- **FX** → Animation (fallback: Layout) + All shot assets
- **Render** → Lighting + All shot assets
- **Comp** → Render (fallback: Lighting) + All shot assets

---

## Implementation Components

### 1. DependencyResolver Service
**File**: `core/dependency_resolver.py`

**Main Method**:
```python
get_dependencies(task_data: dict) -> List[dict]
```

**Returns**:
```python
[
    {
        'source': 'upstream_task' | 'asset_dependency',
        'task': {...},
        'entity': {...},
        'version': {...},
        'attachments': [...],
        'published_files': [...]
    }
]
```

### 2. Dependencies Dialog
**File**: `ui/dialogs/dependencies_dialog.py`

**Features**:
- Tree widget structure (similar to publish dialog file tree)
- Top-level: Dependency categories (Upstream Tasks, Asset Dependencies)
- Second-level: Individual dependencies with version info
- Third-level: Files (attachments + published files)
- Download buttons
- File info display (size, type)

**Tree Structure**:
```
QTreeWidget
├─ QTreeWidgetItem: "Upstream Tasks (1)"
│  └─ QTreeWidgetItem: "Art - v003"
│     ├─ QTreeWidgetItem: "concept_sketch.jpg (2.3 MB)"
│     └─ QTreeWidgetItem: "reference.zip (15.1 MB)"
└─ QTreeWidgetItem: "Asset Dependencies (2)"
   ├─ QTreeWidgetItem: "Character: Cianlu - Rig v005"
   │  └─ QTreeWidgetItem: "cianlu_rig.ma (8.5 MB)"
   └─ QTreeWidgetItem: "Prop: Tablet - Model v002"
      └─ QTreeWidgetItem: "tablet_model.abc (3.2 MB)"
```

### 3. Task Card Context Menu
**File**: `ui/widgets/task_card_widget.py`

**Add to existing context menu**:
```python
def contextMenuEvent(self, event):
    menu = QMenu(self)

    # Existing actions
    view_action = menu.addAction("View Details")
    publish_action = menu.addAction("Publish")

    # NEW: Dependencies action
    dependencies_action = menu.addAction("View Dependencies")

    action = menu.exec_(event.globalPos())

    if action == dependencies_action:
        self._show_dependencies()
```

**New signal**:
```python
dependencies_requested = Signal(dict)  # Emits task_data
```

### 4. Main Window Integration
**File**: `ui/main_window.py`

**Connect signal from task cards**:
```python
def _setup_task_card_connections(self, task_card):
    task_card.publish_requested.connect(self.on_publish_requested)
    task_card.dependencies_requested.connect(self.on_dependencies_requested)  # NEW

@Slot(dict)
def on_dependencies_requested(self, task_data):
    """Open dependencies dialog for task"""
    dialog = DependenciesDialog(
        task_data=task_data,
        dependency_resolver=self.dependency_resolver,
        parent=self
    )
    dialog.exec()
```

---

## Data Flow

```
1. User right-clicks task card
   ↓
2. Context menu shows "View Dependencies"
   ↓
3. Task card emits dependencies_requested signal
   ↓
4. Main window receives signal
   ↓
5. Main window creates DependenciesDialog
   ↓
6. Dialog calls DependencyResolver.get_dependencies()
   ↓
7. Resolver queries ShotGrid:
   a. Get entity tasks
   b. Filter upstream tasks by type
   c. Get latest versions
   d. Get attachments & published files
   e. If shot: Query linked assets
   ↓
8. Dialog builds tree view from results
   ↓
9. User can:
   - Browse dependencies
   - View file details
   - Download files
```

---

## Implementation Steps

### Step 1: DependencyResolver Service
- Create service class
- Implement task type parsing
- Implement pipeline dependency mapping
- Implement upstream task resolution
- Implement asset dependency resolution (for shots)
- Add error handling

### Step 2: Dependencies Dialog
- Create dialog class
- Build tree widget layout
- Implement tree population from dependency data
- Add file info display
- Add download functionality
- Style similar to publish dialog

### Step 3: Task Card Context Menu
- Add "View Dependencies" menu item
- Create dependencies_requested signal
- Emit signal with task_data

### Step 4: Main Window Integration
- Initialize DependencyResolver
- Connect task card signals
- Implement on_dependencies_requested handler
- Test end-to-end workflow

---

## UI Mockup - Dependencies Dialog

```
┌─────────────────────────────────────────────────────┐
│ Dependencies - Asset: generic_prop_1 - Modeling     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ▼ Upstream Tasks (1)                               │
│   ▼ Art - v003                                     │
│     ☐ concept_sketch.jpg               2.3 MB     │
│     ☐ reference_photos.zip            15.1 MB     │
│                                                     │
│ ▼ Asset Dependencies (0)                           │
│   (No asset dependencies for this task)            │
│                                                     │
│                                        [Select All]│
│                                   [Download Selected]│
│                                             [Close]│
└─────────────────────────────────────────────────────┘
```

**For Shot Tasks:**
```
┌─────────────────────────────────────────────────────┐
│ Dependencies - Shot: sq010_050 - Animation          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ▼ Upstream Tasks (1)                               │
│   ▼ Layout - v002                                  │
│     ☐ camera_layout.abc               1.8 MB     │
│     ☐ scene_assembly.ma              12.5 MB     │
│                                                     │
│ ▼ Asset Dependencies (3)                           │
│   ▼ Character: Cianlu - Rig v005                  │
│     ☐ cianlu_rig.ma                   8.5 MB     │
│     ☐ cianlu_controls.json          125 KB     │
│   ▼ Character: MascotaBebe - Rig v003            │
│     ☐ mascota_rig.ma                  6.2 MB     │
│   ▼ Prop: Tablet - Model v002                    │
│     ☐ tablet_model.abc                3.2 MB     │
│                                                     │
│                                        [Select All]│
│                                   [Download Selected]│
│                                             [Close]│
└─────────────────────────────────────────────────────┘
```

---

## Task Type Parsing

Extract task type from content field:
```python
"002_Modeling" → "Modeling"
"02_Animacion" → "Animacion"
"Art" → "Art"
```

Pattern: Remove leading digits and underscores

---

## Next Steps

1. ✅ Review outline
2. Implement DependencyResolver service
3. Create DependenciesDialog UI
4. Add context menu to task cards
5. Wire up signals in main window
6. Test with real ShotGrid data
