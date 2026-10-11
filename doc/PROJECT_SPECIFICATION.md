# MapLoom Project Specification

**Version:** 0.1.0  
**Status:** Phase 1 - Core Implementation  
**Last Updated:** 2026-10-11

---

## 1. Project Overview

### Purpose
MapLoom is a desktop application for viewing MBTiles map files and generating missing zoom levels through intelligent interpolation and resampling.

### Target Users
- GIS professionals
- Map tile developers
- Anyone needing to fill gaps in zoom level coverage

### Key Problem Solved
MBTiles files often have incomplete zoom level coverage (e.g., Z8, Z10, Z12, Z14, Z16 but missing Z9, Z11, Z13, Z15). MapLoom generates the missing levels intelligently.

---

## 2. Functional Requirements

### 2.1 MBTiles File Reading
- **Req 2.1.1:** Read and parse MBTiles SQLite database files
- **Req 2.1.2:** Extract and display file metadata:
  - File name
  - Human-readable name (from metadata table)
  - Description
  - Format (png, jpg, webp, pbf, etc.)
  - Bounds (min/max zoom coverage)
  - Center point coordinates (if available)
- **Req 2.1.3:** List all available zoom levels (original only)
- **Req 2.1.4:** Calculate file statistics (tile count, database size)

### 2.2 Characteristics Display (Left Panel)
- **Req 2.2.1:** Scrollable left panel showing all file metadata
- **Req 2.2.2:** Display zoom levels in a sortable list
- **Req 2.2.3:** Visual indicators for original vs generated zoom levels:
  - Original: standard color/icon
  - Generated: different color + special icon
- **Req 2.2.4:** Allow user to edit metadata (when appropriate)
- **Req 2.2.5:** Show file statistics (total tiles, size)

### 2.3 Zoom Level Generation
- **Req 2.3.1:** Detect missing zoom levels between min and max
- **Req 2.3.2:** Generate missing levels using:
  - **Interpolation:** If adjacent zoom levels exist, interpolate
  - **Downsampling:** If only higher zoom exists, downsample tiles
- **Req 2.3.3:** Handle edge cases:
  - Warn user if generating beyond max zoom (quality degrades)
  - Require user confirmation for edge cases
  - Allow user override with warning
- **Req 2.3.4:** Track which zoom levels are generated vs original

### 2.4 Tile Processing
- **Req 2.4.1:** Read tiles from MBTiles database (from tiles table)
- **Req 2.4.2:** Resample tiles using PIL (Pillow):
  - Downsampling: Use LANCZOS for quality
  - Upsampling: Use LANCZOS for clarity
- **Req 2.4.3:** Preserve tile format (PNG, JPEG, WebP, etc.)
- **Req 2.4.4:** Handle tile coordinate conversions:
  - Support both XYZ and TMS coordinate systems
  - Convert as needed for resampling

### 2.5 Progress Indication
- **Req 2.5.1:** Show progress during zoom generation:
  - Tile-count based (e.g., "1,245 / 5,000 tiles")
  - Can be changed to percentage if needed
- **Req 2.5.2:** Provide cancel button with graceful handling
- **Req 2.5.3:** Show estimated time remaining
- **Req 2.5.4:** Update characteristics panel when complete

### 2.6 Map Viewer (Right Panel)
- **Req 2.6.1:** Display map tiles from MBTiles file
- **Req 2.6.2:** Interactive pan and zoom controls
- **Req 2.6.3:** Show center point if available
- **Req 2.6.4:** Support different tile coordinate systems

### 2.7 Configuration
- **Currently:** Keep simple (no settings file)
- **Future:** Ready to add YAML-based settings when needed

---

## 3. Technical Requirements

### 3.1 Architecture
- **Language:** Python 3.10+
- **GUI Framework:** PyQt5 5.15.7
- **Image Processing:** Pillow 12.3.0
- **Database:** SQLite 3 (standard library)
- **Testing:** pytest 7.4.3

### 3.2 Database Schema (MBTiles)
MBTiles files use SQLite with required tables:

**metadata table:**
```sql
CREATE TABLE metadata (
    name TEXT PRIMARY KEY,
    value TEXT
);
```

Standard keys:
- `name` - Human-readable name
- `description` - File description
- `version` - Schema version (usually 1.1 or 1.2)
- `type` - overlay or baselayer
- `format` - png, jpg, webp, pbf, etc.
- `bounds` - min/max coordinates (west,south,east,north)
- `center` - center coordinates (lon,lat,zoom)
- `minzoom` - Minimum zoom level
- `maxzoom` - Maximum zoom level

**tiles table:**
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

### 3.3 Coordinate Systems
- **XYZ:** Web Mercator (used by most web maps)
  - (0,0) at top-left
  - Y increases downward
- **TMS:** Tile Map Service
  - (0,0) at bottom-left
  - Y increases upward
- MBTiles uses TMS by default, must convert for display

### 3.4 Tile Processing
- **Input:** PNG/JPEG/WebP blob from database
- **Process:** Resample using PIL
- **Output:** Same format to new zoom level
- **Quality:** Use LANCZOS filter (best for maps)

### 3.5 File Structure

```
src/
├── core/
│   ├── mbtiles_reader.py       # Read MBTiles files
│   ├── zoom_generator.py       # Generate missing zooms
│   └── tile_processor.py       # Resample tiles
├── map/
│   ├── tile_server.py          # Serve tiles from db
│   └── map_renderer.py         # Render map display
└── gui/
    ├── widgets/
    │   ├── characteristics_panel.py
    │   ├── map_viewer.py
    │   └── progress_widget.py
    └── dialogs/
        └── zoom_generation_progress_dialog.py
```

---

## 4. User Interface Design

### 4.1 Main Window Layout
```
┌───────────────────────────────────────────────┐
│ MapLoom - Filename.mbtiles                    │
├───────────────────────────────────────────────┤
│ File  Help                                    │ ← Menu bar
├───────────────────────────────────────────────┤
│ [📁 Open] [Generate Zoom] [Settings]  Status  │ ← Toolbar
├─────────────────┬───────────────────────────┤
│                 │                           │
│ Characteristics │ Map Viewer                │
│     Panel       │ (Right)                   │
│   (Left)        │                           │
│                 │ • Pan/Zoom Controls       │
│ • File Info     │ • Map Display             │
│ • Zoom List     │ • Center Point            │
│ • Statistics    │                           │
│                 │                           │
├─────────────────┴───────────────────────────┤
│ Ready - File loaded, no changes              │ ← Status bar
└───────────────────────────────────────────────┘
```

### 4.2 Characteristics Panel (Left)
**Scrollable area showing:**
- File Information
  - Name
  - Description
  - Format
  - Size
- Map Bounds
  - North, South, East, West
  - Center point
- Zoom Levels
  - List with original vs generated indicators
  - Tile counts per zoom
- Statistics
  - Total tiles
  - Database size

### 4.3 Map Viewer (Right)
**Interactive map showing:**
- Tile display from MBTiles
- Pan (click and drag)
- Zoom in/out buttons
- Center point marker
- Zoom level indicator

### 4.4 Zoom Generation Dialog
**When user clicks "Generate Zoom":**
- Select which zoom levels to generate
- Show quality warnings for edge cases
- Progress bar (tile-count based)
- Cancel button
- Estimated time remaining

---

## 5. Zoom Generation Algorithm

### 5.1 Algorithm Overview

```
IF user requests zoom Z:
  IF Z exists:
    Return error (already exists)
  
  IF Z < min_zoom OR Z > max_zoom + 2:
    Return error (not possible)
  
  IF Z > max_zoom:
    Warn user about quality degradation
    Require confirmation
  
  Source_zoom = Z + 1 (one level higher)
  IF Source_zoom exists:
    Use DOWNSAMPLING from Source_zoom
  ELSE:
    Source_zoom = Z - 1 (one level lower)
    IF Source_zoom exists:
      Use INTERPOLATION or UPSAMPLING
    ELSE:
      Find nearest zoom level with data
      Use appropriate resampling
  
  Generate tiles for zoom Z
  Write to MBTiles database
  Update metadata
  Mark as generated
```

### 5.2 Downsampling (from higher zoom)
- Take 4 tiles at zoom Z+1
- Combine into 1 tile at zoom Z
- Resample using LANCZOS filter
- Preserve aspect ratio

### 5.3 Interpolation (between zooms)
- Average data from adjacent zoom levels
- Blend tiles for smooth transitions
- Handle edge tiles specially

### 5.4 Quality Considerations
- Downsampling reduces detail (acceptable, expected)
- Upsampling beyond 2 levels shows degradation (warn user)
- Best quality: generate from closest available level

---

## 6. Error Handling

### 6.1 File Loading Errors
- File not found → Show dialog, suggest alternatives
- Not an MBTiles file → Validate schema, show error
- Database locked → Suggest closing other apps
- Corrupted metadata → Show what's readable, warn about missing

### 6.2 Zoom Generation Errors
- Insufficient source data → Suggest alternative
- Database write error → Show error, suggest disk space check
- Invalid zoom level → Prevent generation, show constraints
- Cancelled by user → Clean up partial data, return to ready state

### 6.3 Tile Processing Errors
- Unsupported format → Show error, skip tile
- Corrupted tile data → Show warning, skip tile
- Memory issues → Show error, suggest smaller batch

---

## 7. Testing Strategy

### 7.1 Unit Tests
- MBTiles reader:
  - Read valid files
  - Handle missing metadata
  - Parse bounds and center correctly
- Zoom generator:
  - Detect missing levels correctly
  - Select appropriate source zoom
  - Handle edge cases
- Tile processor:
  - Downsample tiles correctly
  - Preserve formats
  - Handle coordinate conversions

### 7.2 Integration Tests
- Load file → read metadata → display
- Generate zoom → write to DB → verify
- Full workflow from loading to generation

### 7.3 Test Data
- Sample MBTiles files with various configurations
- Edge cases: single zoom, all zooms, gaps at edges
- Different formats: PNG, JPEG, WebP

---

## 8. Success Criteria

### Phase 1 (Current)
- ✅ GUI structure with menu and toolbar
- ✅ File loading dialog
- ✅ MBTiles reader implemented
- ✅ Characteristics panel displays file info
- ✅ Zoom levels displayed with original indicator

### Phase 2
- [ ] Zoom generation algorithm implemented
- [ ] Progress dialog with cancellation
- [ ] Tile resampling working

### Phase 3
- [ ] Map viewer displaying tiles
- [ ] Pan and zoom controls
- [ ] Center point display

### Phase 4
- [ ] Complete test coverage
- [ ] UI refinements based on testing
- [ ] Documentation complete

---

## 9. Known Constraints

### 9.1 File Handling
- MBTiles files are SQLite databases (single file, must have .mbtiles extension)
- Cannot modify while generating (file is locked)
- Large files (>2GB) may be slow

### 9.2 Tile Limits
- Maximum practical zooms: Z0-Z20+ (most files Z0-Z18)
- Maximum tiles per zoom: ~256²·2^(z·2) at zoom z
- Memory considerations for large zoom generations

### 9.3 Platform Support
- Linux: Primary target
- macOS: Should work (not tested)
- Windows: Should work (not tested)

---

## 10. Future Enhancements

- [ ] Settings file (YAML) for preferences
- [ ] Batch processing (multiple files)
- [ ] Export to GeoTIFF
- [ ] Advanced resampling algorithms
- [ ] Tile validation and repair
- [ ] Performance metrics and reporting
- [ ] Dark mode UI
- [ ] Command-line interface

---

## 11. Glossary

| Term | Definition |
|------|-----------|
| **MBTiles** | SQLite database format for storing map tiles |
| **Zoom Level** | Z value (0-20+), Z0 is whole world, higher = more detail |
| **Tile** | 256×256 pixel image at specific (zoom, x, y) coordinates |
| **Metadata** | Information about the map (name, description, bounds, etc.) |
| **Interpolation** | Generate intermediate data between known points |
| **Downsampling** | Reduce resolution by combining tiles |
| **TMS** | Tile Map Service (coordinate system used by MBTiles) |
| **XYZ** | Web Mercator tile coordinates (different Y axis than TMS) |

---

**Document Status:** ✅ Ready for Implementation  
**Next:** Begin Phase 1 with MBTiles reader implementation
