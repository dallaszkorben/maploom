# MapLoom - MBTiles Viewer and Zoom Level Generator

**Status:** Project Structure Phase  
**Created:** 2026-10-11  
**Python Version:** 3.10+  
**Framework:** PyQt5

---

## Overview

MapLoom is a desktop application for viewing MBTiles map files and generating missing zoom levels through intelligent interpolation and resampling.

### Key Features

- **MBTiles File Viewer**
  - Read and display MBTiles map characteristics
  - Show file metadata: name, description, format, bounds, center
  - Display available zoom levels

- **Characteristics Display**
  - Left panel: Scrollable characteristics with human-readable information
  - Edit/modify file properties
  - Visual indicators for original vs generated zoom levels

- **Zoom Level Generation**
  - Generate missing zoom levels using interpolation
  - Intelligent tile resampling (downsampling from higher zoom levels)
  - Edge case handling with user warnings
  - Progress indicator with tile count
  - Cancellable operations

- **Interactive Map**
  - Right panel: MBTiles-based map viewer
  - Pan and zoom controls
  - Display default center point if available

---

## Project Structure

```
MapLoom/
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── mbtiles_reader.py     # MBTiles file reading
│   │   ├── zoom_generator.py     # Zoom level generation algorithm
│   │   └── tile_processor.py     # Tile resampling and interpolation
│   ├── map/                      # Map tile handling
│   │   ├── __init__.py
│   │   ├── tile_server.py        # In-memory tile serving
│   │   └── map_renderer.py       # Map rendering utilities
│   └── gui/                      # PyQt5 GUI components
│       ├── __init__.py
│       ├── main_window.py        # Main application window
│       ├── widgets/              # Custom widgets
│       │   ├── __init__.py
│       │   ├── characteristics_panel.py
│       │   ├── map_viewer.py
│       │   ├── zoom_generator_dialog.py
│       │   └── progress_widget.py
│       └── dialogs/              # Dialog windows
│           ├── __init__.py
│           └── zoom_generation_progress_dialog.py
├── config/                       # Configuration
│   └── __init__.py
├── doc/                          # Documentation
│   ├── README.md                 # This file
│   ├── ARCHITECTURE.md           # System design
│   ├── PROJECT_SPECIFICATION.md  # Requirements
│   ├── ZOOM_GENERATION_ALGORITHM.md  # Algorithm details
│   ├── HARD_PROBLEMS_AND_SOLUTIONS.md # Issues & solutions
│   └── TODO_LIST.md              # Development tasks
├── tests/                        # Unit tests
│   ├── __init__.py
│   └── test_*.py                 # Test files
├── mbtiles/                      # Sample MBTiles files
├── images/                       # Application images/icons
├── venv/                         # Python virtual environment
├── requirements.txt              # Python dependencies
├── activate_venv.sh              # Virtual environment activation script
└── .gitignore                    # Git ignore patterns

```

---

## Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd /home/akoel/Projects/boat/general/Code/MapLoom

# Activate virtual environment
source activate_venv.sh

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import PyQt5; import PIL; print('✅ All dependencies installed')"
```

### 2. Run Application

```bash
# From project root directory
python src/main.py

# With debug logging
python src/main.py --debug

# With specific file
python src/main.py --file path/to/map.mbtiles
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_zoom_generator.py
```

---

## Documentation Guide

### For Understanding the Project

Start here in order:

1. **[PROJECT_SPECIFICATION.md](doc/PROJECT_SPECIFICATION.md)** (10 min)
   - What the project does
   - User requirements
   - System capabilities

2. **[ARCHITECTURE.md](doc/ARCHITECTURE.md)** (15 min)
   - How the system is organized
   - Component relationships
   - Data flow

3. **[ZOOM_GENERATION_ALGORITHM.md](doc/ZOOM_GENERATION_ALGORITHM.md)** (20 min)
   - How zoom levels are generated
   - Interpolation and resampling approach
   - Edge case handling

### For Development

- **[TODO_LIST.md](doc/TODO_LIST.md)** - Step-by-step development tasks
- **[HARD_PROBLEMS_AND_SOLUTIONS.md](doc/HARD_PROBLEMS_AND_SOLUTIONS.md)** - Known issues and solutions

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt5 | 5.15.7 | GUI framework |
| PyQtWebEngine | 5.15.7 | Map rendering |
| Pillow | 12.3.0 | Tile image processing |
| PyYAML | 6.0.1 | Configuration (future) |
| pytest | 7.4.3 | Unit testing |

All dependencies are pinned to exact versions for reproducibility.

---

## Key Concepts

### MBTiles Format

MBTiles is a specification for storing map tiles in a single SQLite database file.

- **Tiles Table:** Stores individual tile images (blob data)
- **Metadata Table:** Stores file metadata (name, description, bounds, center, etc.)
- **Zoom Levels:** Typically Z0 (entire world) to Z20+ (street level)

### Zoom Level Generation

The application can generate missing zoom levels:

1. **Interpolation:** If Z13 is missing but Z12 and Z14 exist, interpolate
2. **Downsampling:** If only Z14 exists, resample Z14 tiles to generate Z13
3. **Edge Cases:** Warn user if generating beyond highest zoom (quality degradation)

### Display Differentiation

Generated zoom levels are shown differently than original ones:

- **Color/Icon:** Visual indicator on characteristics panel
- **Metadata:** Additional field tracking original vs generated
- **UI Feedback:** Clear indication of zoom level source

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Main Window (PyQt5)                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐    ┌──────────────────────┐  │
│  │ Characteristics  │    │   Map Viewer Panel   │  │
│  │    (Left)        │    │     (Right)          │  │
│  │                  │    │                      │  │
│  │  - File Info     │    │  - Interactive Map   │  │
│  │  - Zoom Levels   │    │  - Pan/Zoom Controls │  │
│  │  - Edit Controls │    │  - Tile Rendering    │  │
│  │  - Progress Bar  │    │                      │  │
│  └──────────────────┘    └──────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
         ↓                            ↓
    ┌─────────────────────────────────────────┐
    │   Core Logic (src/core/)                │
    ├─────────────────────────────────────────┤
    │ - MBTiles Reader                        │
    │ - Zoom Level Generator (Algorithm)      │
    │ - Tile Processor (Resampling)           │
    └─────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────┐
    │   Map Handler (src/map/)                │
    ├─────────────────────────────────────────┤
    │ - Tile Server                           │
    │ - Map Rendering Utilities               │
    └─────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────┐
    │   MBTiles File (SQLite Database)        │
    └─────────────────────────────────────────┘
```

---

## Development Workflow

### Adding a New Feature

1. Check **[TODO_LIST.md](doc/TODO_LIST.md)** for step description
2. Read relevant documentation (ARCHITECTURE, etc.)
3. Implement feature following code patterns
4. Write/update tests in `tests/`
5. Document any decisions in **HARD_PROBLEMS_AND_SOLUTIONS.md**
6. Verify acceptance criteria from TODO_LIST

### Debugging

If something isn't working:

1. Check **[HARD_PROBLEMS_AND_SOLUTIONS.md](doc/HARD_PROBLEMS_AND_SOLUTIONS.md)**
2. Enable debug logging: `python src/main.py --debug`
3. Check `maploom.log` for detailed output
4. Add to HARD_PROBLEMS_AND_SOLUTIONS if novel issue

---

## File Locations

| Item | Location |
|------|----------|
| MBTiles samples | `/MapLoom/mbtiles/` |
| Application log | `/MapLoom/maploom.log` |
| Tests | `/MapLoom/tests/` |
| Configuration (future) | `/MapLoom/config/` |

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2026-10-11 | Initial project structure |

---

## Next Steps

1. ✅ Project structure created
2. ⏳ Phase 1: Core MBTiles reader implementation
3. ⏳ Phase 2: Characteristics panel GUI
4. ⏳ Phase 3: Map viewer integration
5. ⏳ Phase 4: Zoom generation algorithm
6. ⏳ Phase 5: Progress UI and refinement

---

## Contact & Questions

For documentation questions:
- Check the relevant doc file
- Review cross-references
- Check TODO_LIST.md for context

For code questions:
- Check comments in the code
- Review HARD_PROBLEMS_AND_SOLUTIONS.md
- Check ARCHITECTURE.md for system design
