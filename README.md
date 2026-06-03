# Kukari Pipeline — Shotgrid Manager

A desktop pipeline tool for **Kukari Animation Studio** that integrates directly with ShotGrid (Autodesk Flow) to help artists manage their tasks, publish work, and navigate pipeline dependencies — all from a single application.

---

## Overview

Shotgrid Manager is a PySide6 desktop application that replaces the need to use the ShotGrid web interface for day-to-day production tasks. It presents each artist's assigned tasks on a Kanban-style board, lets them drag tasks between pipeline stages, publish files directly from the app, and inspect what upstream work their current task depends on.

---

## Features

### Task Board
- Kanban board showing tasks grouped by status: **To Do**, **In Progress**, **In Review**, **Done**
- Drag-and-drop cards between columns to update task status in ShotGrid
- Optimistic updates — the UI responds instantly; ShotGrid is synced in the background
- Local data model caches all tasks on load; filtering and search run entirely in memory for instant response without extra API calls
- Filter toolbar to narrow tasks by project, entity type (Asset / Shot), task name, or free-text search

### Publishing Workflow
- Publish dialog accessible from any task card
- Supports single-file and multi-file publishes under one version
- Folder publishing: folders are automatically zipped before upload
- Files are categorised as editable files, single delivery, or multiple delivery (renders)
- Each publish creates a **Version** entity and one **PublishedFile** entity per file, and links the uploaded attachment to the task, version, and published file
- Version numbers are auto-incremented per task (v001, v002, …)
- Optionally sets task status to final on successful publish

### Dependency Resolver
- Inspects any task and returns its upstream pipeline dependencies
- For **Asset** tasks follows the asset pipeline: Art → Model → Rig / Surfacing / Texture → Character FX / LightRig → Render → Delivery
- For **Shot** tasks follows the shot pipeline: Layout → Animation → Lighting / CFX / FX → Render → Comp, and additionally resolves the linked assets for the shot (preferring Rig, falling back to Model)
- Shows the latest valid version and its published files for each dependency, or a warning if no approved version exists yet

### Cross-platform Build
PyInstaller build scripts are included for Windows, Linux, and macOS to produce a standalone executable with no Python installation required on artist machines.

---

## Architecture

```
shotgrid_manager/
├── src/
│   ├── main.py                         # Application entry point
│   ├── config/
│   │   ├── settings.py                 # App-level settings
│   │   └── shotgrid_config.py          # ShotGrid connection config
│   ├── core/
│   │   ├── shotgrid_instance.py        # Shared persistent ShotGrid connection
│   │   ├── base_manager.py             # Base class for all entity managers
│   │   ├── task_manager.py             # Task CRUD + queries
│   │   ├── asset_manager.py            # Asset queries
│   │   ├── shot_manager.py             # Shot queries
│   │   ├── version_manger.py           # Version creation and queries
│   │   ├── published_file_manager.py   # PublishedFile entity management
│   │   ├── attachment_manager.py       # File upload to ShotGrid
│   │   ├── publishing_service.py       # High-level publish workflow orchestrator
│   │   ├── dependency_resolver.py      # Pipeline dependency resolution
│   │   └── path_builder.py             # Local filesystem path helpers
│   ├── ui/
│   │   ├── main_window.py              # Main window, wires managers to UI
│   │   ├── dialogs/
│   │   │   ├── publish_dialog.py       # Multi-file publish dialog
│   │   │   └── dependencies_dialog.py  # Dependency viewer dialog
│   │   └── widgets/
│   │       ├── kanban_task_board_widget.py   # Kanban board container
│   │       ├── task_column_widget.py          # Single status column
│   │       ├── task_card_widget.py            # Individual task card
│   │       ├── filter_toolbar_widget.py       # Project/type/search filters
│   │       └── shotgrid_task_data_model.py    # Local cache and filter model
│   └── utils/
│       ├── logger.py                   # Logging setup
│       ├── progress_tracker.py         # Step-based progress reporting
│       ├── validators.py               # Input validation helpers
│       └── zip_utility.py              # Cross-platform folder compression
└── build/
    ├── build_windows.py
    ├── build_macos.py
    └── build_linus.py
```

All core managers share a single `ShotgridInstance` (persistent connection), instantiated once in `MainWindow` and passed down to every manager and service.

---

## Requirements

- Python 3.10+
- PySide6
- shotgun-api3
- A ShotGrid site with script-based API access

---

## Configuration

The application is configured via environment variables:

| Variable | Required | Description |
|---|---|---|
| `SG_URL` | Yes | ShotGrid site URL (e.g. `https://studio.shotgrid.autodesk.com`) |
| `SG_SCRIPT_NAME` | Yes | API script name created in ShotGrid Admin |
| `SG_SCRIPT_KEY` | Yes | API key for the script |
| `KUKARI_USER_ID` | Yes | ShotGrid HumanUser ID for the logged-in artist |
| `WORK_AREA` | No | Local root path for resolving file paths |

---

## Running

```bash
cd shotgrid_manager/src
python main.py
```

---

## Building a Standalone Executable

```bash
# Windows
python shotgrid_manager/build/build_windows.py

# macOS
python shotgrid_manager/build/build_macos.py

# Linux
python shotgrid_manager/build/build_linus.py
```

The output executable bundles Python, PySide6, and shotgun-api3 so artists can run it without any local Python setup.
