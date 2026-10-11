# MapLoom Architecture

**Version:** 0.1.0  
**Status:** Phase 1 Complete  
**Last Updated:** 2026-10-11

---

## 1. System Overview

MapLoom is a desktop application for viewing MBTiles map files and generating missing zoom levels through intelligent interpolation and resampling.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PyQt5 GUI Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  MainWindow (main_window.py)                                    │
│  ├─ CharacteristicsPanel (characteristics_panel.py)             │
│  ├─ MapViewer (map_viewer.py)                                   │
│  └─ ProgressDialog (zoom_generation_progress_dialog.py)         │
├─────────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Core Module (src/core/)                                        │
│  ├─ MBTilesReader (mbtiles_reader.py)                           │
│  ├─ ZoomGenerator (zoom_generator.py) [TODO]                    │
│  └─ TileProcessor (tile_processor.py) [TODO]                    │
│                                                                 │
│  Map Module (src/map/)                                          │
│  ├─ TileServer (tile_server.py) [TODO]                          │
│  └─ MapRenderer (map_renderer.py) [TODO]                        │
├─────────────────────────────────────────────────────────────────┤
│                     Data Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  MBTiles File (SQLite Database)                                 │
│  ├─ metadata table (name, description, format, bounds, etc.)   │
│  └─ tiles table (zoom_level, tile_column, tile_row, tile_data) │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
MapLoom/
├── src/
│   ├── main.py                         # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── mbtiles_reader.py           # Read MBTiles files (✅ COMPLETE)
│   │   ├── zoom_generator.py           # Generate zooms (TODO)
│   │   └── tile_processor.py           # Resample tiles (TODO)
│   ├── map/
│   │   ├── __init__.py
│   │   ├── tile_server.py              # Serve tiles (TODO)
│   │   └── map_renderer.py             # Render map (TODO)
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py              # Main UI (✅ COMPLETE)
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── characteristics_panel.py # Left panel (✅ COMPLETE)
│       │   ├── map_viewer.py            # Map display (TODO)
│       │   └── progress_widget.py       # Progress UI (TODO)
│       └── dialogs/
│           ├── __init__.py
│           └── zoom_generation_progress_dialog.py (TODO)
├── config/
│   └── __init__.py                     # Configuration (for future)
├── tests/                              # Unit tests
├── doc/                                # Documentation
├── mbtiles/                            # Sample files
├── images/                             # Icons/assets
└── venv/                               # Virtual environment
```

---

## 3. Component Description

### 3.1 GUI Layer

#### MainWindow (`src/gui/main_window.py`)
**Responsibilities:**
- Create and manage main application window
- Handle file loading and menu actions
- Coordinate between characteristics panel and map viewer
- Manage window state and layout

**Key Methods:**
- `load_mbtiles_file()` - Load and display MBTiles file
- `open_file_dialog()` - File browser dialog
- `_setup_ui()` - Create UI components
- `_create_menu_bar()` - Create menus
- `_create_toolbar()` - Create toolbar

**Signals:**
- `file_loaded` - Emitted when file successfully loaded

#### CharacteristicsPanel (`src/gui/widgets/characteristics_panel.py`)
**Responsibilities:**
- Display file metadata and statistics
- Show zoom levels with original/generated indicators
- Provide scrollable interface for all content
- Handle missing/empty fields gracefully

**Key Methods:**
- `load_mbtiles()` - Load and display file info
- `_setup_ui()` - Create panel layout
- `clear()` - Clear all displayed data

**Signals:**
- `zoom_selected` - Emitted when user clicks zoom level

#### MapViewer (`src/gui/widgets/map_viewer.py`) [TODO]
**Responsibilities:**
- Display map tiles from MBTiles
- Handle pan and zoom interactions
- Show center point
- Display zoom level indicator

#### ProgressDialog (`src/gui/dialogs/zoom_generation_progress_dialog.py`) [TODO]
**Responsibilities:**
- Show zoom generation progress
- Display tile count progress
- Provide cancel button
- Show status messages

### 3.2 Business Logic Layer

#### MBTilesReader (`src/core/mbtiles_reader.py`)
**Responsibilities:**
- Read and validate MBTiles SQLite database
- Extract metadata from metadata table
- List zoom levels from tiles table
- Calculate statistics and detect gaps

**Key Classes:**
- `MBTilesMetadata` - Dataclass for metadata
- `ZoomLevelInfo` - Dataclass for zoom info
- `MBTilesReader` - Main reader class

**Key Methods:**
- `get_metadata()` - Return file metadata
- `get_zoom_levels()` - Return zoom level list
- `get_available_zooms()` - Return zoom numbers
- `get_missing_zooms()` - Return gap zooms
- `get_file_statistics()` - Return file stats
- `get_tile()` - Read individual tile
- `mark_zoom_as_generated()` - Track generated zooms

**Input:** MBTiles file path  
**Output:** Parsed metadata, zoom info, statistics

#### ZoomGenerator (`src/core/zoom_generator.py`) [TODO]
**Responsibilities:**
- Implement zoom generation algorithm
- Select appropriate source zoom
- Detect edge cases (quality issues)
- Handle user warnings and confirmations

**Key Methods:**
- `analyze_zoom_gaps()` - Detect missing zooms
- `calculate_best_source()` - Find source zoom
- `should_warn_user()` - Check quality issues
- `generate_zoom()` - Generate specific zoom level

**Input:** MBTiles file, target zoom level  
**Output:** Status, warnings, success/failure

#### TileProcessor (`src/core/tile_processor.py`) [TODO]
**Responsibilities:**
- Read tiles from source zoom
- Resample tiles to target zoom
- Write tiles to database
- Handle different image formats

**Key Methods:**
- `downsample_tiles()` - Reduce resolution
- `upsample_tiles()` - Increase resolution
- `write_tiles()` - Save to database
- `convert_format()` - Handle image formats

**Input:** Tiles, zoom info  
**Output:** Resampled tiles

#### TileServer (`src/map/tile_server.py`) [TODO]
**Responsibilities:**
- Serve tiles to map viewer
- Cache frequently accessed tiles
- Convert coordinates between systems
- Handle missing tiles

**Input:** Zoom, x, y coordinates  
**Output:** Tile image data

#### MapRenderer (`src/map/map_renderer.py`) [TODO]
**Responsibilities:**
- Render tiles on map canvas
- Calculate tile positions
- Handle projection (Web Mercator)
- Composite tiles into view

---

## 4. Data Flow

### 4.1 File Loading Flow

```
User clicks "Open MBTiles File"
        ↓
File dialog opens (remembers last folder)
        ↓
User selects .mbtiles file
        ↓
MainWindow.load_mbtiles_file() called
        ↓
MBTilesReader reads file
        ├─ Validate SQLite structure
        ├─ Read metadata table
        ├─ Read tiles table
        └─ Calculate statistics
        ↓
CharacteristicsPanel.load_mbtiles() called
        ├─ Update file info display
        ├─ Update zoom level list
        └─ Update statistics display
        ↓
User sees all file information
```

### 4.2 Zoom Generation Flow [TODO]

```
User clicks "Generate Zoom"
        ↓
Dialog shows available options
        ↓
User selects zoom level(s) to generate
        ↓
ZoomGenerator analyzes gaps
        ├─ Find missing zooms
        └─ Calculate quality issues
        ↓
If edge case:
        ├─ Show warning dialog
        └─ Get user confirmation
        ↓
Progress dialog shows (tile-count based)
        ↓
TileProcessor generates tiles
        ├─ Read source tiles
        ├─ Resample using PIL
        └─ Write to database
        ↓
CharacteristicsPanel refreshes
        ├─ Show new generated zooms
        └─ Update statistics
        ↓
User sees new zoom levels available
```

### 4.3 Map Viewing Flow [TODO]

```
Map viewer initialized
        ↓
User pans (click and drag)
        ├─ Calculate new viewport
        └─ Determine needed tiles
        ↓
TileServer fetches tiles
        ├─ Query MBTiles
        ├─ Cache results
        └─ Handle missing tiles
        ↓
MapRenderer composites tiles
        ├─ Calculate positions
        ├─ Apply projections
        └─ Draw on canvas
        ↓
Map display updates
```

---

## 5. Key Design Patterns

### 5.1 Separation of Concerns

**GUI Layer** - Only handles UI display and user interaction  
**Business Logic** - Handles file operations and algorithms  
**Data Layer** - Handles database access

Each layer independent and testable.

### 5.2 Signal-Slot Pattern

PyQt5 signals used for loose coupling:
- `file_loaded` signal emitted when file loads
- `zoom_selected` signal emitted on zoom click
- Handlers update other components without direct dependencies

### 5.3 Dataclasses for Data

- `MBTilesMetadata` - Type-safe metadata container
- `ZoomLevelInfo` - Type-safe zoom info

Benefits: Type hints, immutability, clean data passing

### 5.4 Error Handling Strategy

**File Operations:**
- Validate file structure before processing
- Handle missing fields gracefully (show "not set in file")
- Provide clear error messages to user

**Zoom Generation:**
- Warn user about quality issues
- Require confirmation for risky operations
- Clean up partial data on cancellation

---

## 6. Coordinate Systems

### 6.1 TMS (Tile Map Service)

Used by MBTiles specification:
- (0,0) at bottom-left
- Y increases upward
- Standard for web maps

### 6.2 XYZ (Web Mercator)

Used by most web mapping libraries:
- (0,0) at top-left
- Y increases downward

### 6.3 Conversion

```python
# TMS to XYZ
xyz_y = (2 ** zoom) - 1 - tms_y

# XYZ to TMS
tms_y = (2 ** zoom) - 1 - xyz_y
```

**Important:** MBTiles uses TMS, so conversion needed for display.

---

## 7. Database Schema

### 7.1 Metadata Table

```sql
CREATE TABLE metadata (
    name TEXT PRIMARY KEY,
    value TEXT
);
```

**Standard fields:**
- `name` - Human-readable name
- `description` - Tileset description
- `format` - png, jpg, webp, pbf, etc.
- `bounds` - "west,south,east,north"
- `center` - "lon,lat[,zoom]"
- `minzoom` - Minimum zoom level
- `maxzoom` - Maximum zoom level
- `type` - "overlay" or "baselayer"
- `version` - MBTiles version
- `attribution` - Attribution text

### 7.2 Tiles Table

```sql
CREATE TABLE tiles (
    zoom_level INTEGER,
    tile_column INTEGER,
    tile_row INTEGER,
    tile_data BLOB,
    PRIMARY KEY (zoom_level, tile_column, tile_row)
);
CREATE INDEX idx_tile_zoom ON tiles(zoom_level);
```

**Fields:**
- `zoom_level` - Z value (0-20+)
- `tile_column` - X coordinate (0 to 2^zoom - 1)
- `tile_row` - Y coordinate (0 to 2^zoom - 1, in TMS format)
- `tile_data` - Tile image (PNG, JPEG, WebP, etc.)

---

## 8. Performance Considerations

### 8.1 Tile Caching

- Cache recently accessed tiles in memory
- Reduce database queries for repeated requests
- Use LRU eviction for memory management

### 8.2 Database Indexing

- Index on zoom_level for fast queries
- Consider compound index for (zoom_level, tile_column, tile_row)

### 8.3 Batch Operations

- Process multiple tiles in batches during generation
- Reduces transaction overhead
- Improves generation speed

### 8.4 Image Processing

- Use LANCZOS filter for best quality
- Resample in-memory using PIL
- Avoid unnecessary format conversions

---

## 9. Error Handling

### 9.1 File Errors

**File not found:**
- Show dialog with helpful message
- Suggest checking file path

**Not a valid MBTiles:**
- Check SQLite structure
- Show what's missing (metadata table, tiles table)

**Database locked:**
- Notify user another app has file open
- Suggest closing other apps

### 9.2 Zoom Generation Errors

**Missing source tiles:**
- Suggest alternative zoom level
- Explain why source can't be used

**Quality degradation:**
- Warn user before generation
- Let user decide to proceed

**User cancellation:**
- Stop generation
- Clean up partial data
- Return to ready state

### 9.3 Display Errors

**Missing tiles during view:**
- Show placeholder/checkerboard
- Continue displaying other tiles

**Rendering errors:**
- Log error details
- Show error message in status bar
- Allow user to continue

---

## 10. Testing Strategy

### 10.1 Unit Tests

**MBTilesReader:**
- Test with valid files
- Test with missing metadata
- Test with various zoom configurations
- Test missing field handling

**ZoomGenerator:**
- Test gap detection
- Test source zoom selection
- Test edge case warnings

**TileProcessor:**
- Test downsampling
- Test format conversion
- Test database writes

### 10.2 Integration Tests

**File Loading:**
- Load file → read metadata → display

**Zoom Generation:**
- Select zoom → generate → verify written

**Map Display:**
- Load file → pan → zoom → verify tiles

### 10.3 Manual Testing

**Real Files:**
- Test with various MBTiles files
- Test with different completeness levels
- Test with various tile formats

---

## 11. Future Architecture Improvements

### 11.1 Configuration System

- YAML settings file for user preferences
- Default directories, UI settings, etc.

### 11.2 Plugin System

- Support for custom resampling algorithms
- Support for different tile formats

### 11.3 Batch Processing

- Process multiple MBTiles files
- Apply same zoom generation to all

### 11.4 Command-Line Interface

- CLI for batch processing
- Headless mode for scripts

---

## 12. Dependencies

### 12.1 External Libraries

- **PyQt5** - GUI framework
- **Pillow** - Image processing
- **sqlite3** - Database (standard library)
- **PyYAML** - Configuration (for future)

### 12.2 Python Version

- Python 3.10+ required
- Uses type hints and modern syntax

---

## Current Status

### ✅ Complete (Phase 1)
- Project structure
- MBTiles reader
- Characteristics panel
- Main window and UI

### 📋 Planned (Phase 2)
- Zoom generation algorithm
- Tile processor
- Progress dialog

### 🔮 Planned (Phase 3)
- Map viewer
- Tile server
- Map renderer

### 🎯 Planned (Phase 4)
- Full testing
- Documentation
- UI refinement

---

**Document Status:** Ready for Phase 2 Implementation  
**Next Update:** After Phase 2 completion
