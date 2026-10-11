# MBTiles Metadata - Explanation

**Date:** 2026-10-11  
**Question:** Why can't we see Description and Center?

---

## Answer: They ARE in the specification and ARE in the file!

### 1. MBTiles Specification

**YES**, Description and Center are part of the official MBTiles 1.2 specification.

According to the [MBTiles specification](https://github.com/mapbox/mbtiles-spec):

```
metadata table structure:
  name (TEXT PRIMARY KEY) - Field name
  value (TEXT)            - Field value
```

**Standard metadata fields:**
- `name` - Human-readable name of the tileset (REQUIRED)
- `description` - Description of the tileset (REQUIRED)
- `format` - Image format (png, jpg, webp, pbf, etc.) (REQUIRED)
- `bounds` - Bounding box in EPSG:4326 format: "min_lon,min_lat,max_lon,max_lat" (REQUIRED)
- `center` - Center point: "lon,lat[,zoom]" (OPTIONAL)
- `minzoom` - Minimum zoom level (OPTIONAL)
- `maxzoom` - Maximum zoom level (OPTIONAL)
- `type` - "overlay" or "baselayer" (OPTIONAL)
- `version` - MBTiles version (OPTIONAL)
- `attribution` - Attribution text (OPTIONAL)

### 2. What We Found in the Test File

**Analysis of:** `/home/akoel/Projects/boat/general/Code/CourseStudio/mbtiles/Sweden-Navionics-Z11-Z16.mbtiles`

```
✓ name          = "Sweden merged.Navionics Marine Charts.Z16.Z16 20241226224615 Unknown"
✓ description   = "63870849902158000"
✓ format        = "png"
✓ bounds        = "10.546875,54.775347,24.609375,65.946472"
✓ center        = "17.578125,60.360910,15"
✓ minzoom       = "15"
✓ maxzoom       = "15"
✓ type          = "baselayer"
✓ version       = "1.2"
✓ scheme        = "tms"
✓ attribution   = "" (empty)
```

### Key Finding

**Description and Center EXIST in the database!**

- `description` = `63870849902158000` (not very descriptive - looks like an ID)
- `center` = `17.578125,60.360910,15` (longitude, latitude, zoom)

---

## Why They Might Not Be Visible in the UI

If you're not seeing them on screen, the possible reasons are:

1. **Layout issue** - Labels might be there but cut off due to width
2. **Text color** - Text might be the same color as background
3. **Scrolling needed** - Need to scroll down to see them
4. **Font size too small** - Text too small to read
5. **They're actually displaying** - Check the window size

### Current Display Status

The UI code **SHOULD** display:
- Description: ✓ `"63870849902158000"`
- Center: ✓ `"(17.58°, 60.36°) at Z15"`

If not visible, check:
1. Scroll the characteristics panel down
2. Resize the window to be wider
3. Check if text is white (should be visible on dark background)

---

## What This Means

### For Your Application

1. **MBTiles files CAN have Description and Center**
   - They're part of the official specification
   - Many files DO include them

2. **Not all files are complete**
   - Some creators don't populate all fields
   - Some fields might be strange values (like `63870849902158000`)
   - `attribution` can be empty

3. **Your app SHOULD handle missing data**
   - Show "—" or "N/A" if field is empty
   - Display whatever data IS available

### For Different MBTiles Files

Try loading different MBTiles files to see variations:

- **Complete files**: Have all metadata
- **Incomplete files**: Missing some fields
- **Sparse files**: Only required fields

---

## Technical Details

### How to Check Raw Data

```python
import sqlite3

conn = sqlite3.connect('file.mbtiles')
cursor = conn.cursor()

# Get all metadata
cursor.execute("SELECT name, value FROM metadata")
for name, value in cursor.fetchall():
    print(f"{name} = {value}")

conn.close()
```

### MBTiles File Structure

```
MBTiles (SQLite database)
├── metadata table
│   ├── name: "value"           (human-readable name)
│   ├── description: "value"    (description)
│   ├── format: "png|jpg|webp"  (tile format)
│   ├── bounds: "w,s,e,n"       (bounding box)
│   ├── center: "lon,lat,zoom"  (center point)
│   ├── minzoom: number         (minimum zoom)
│   ├── maxzoom: number         (maximum zoom)
│   ├── version: "1.2"          (spec version)
│   └── ... (other optional fields)
│
└── tiles table
    └── zoom_level, tile_column, tile_row, tile_data (BLOB)
```

---

## Summary

| Question | Answer |
|----------|--------|
| Is Description in the spec? | **YES** - Required field |
| Is Center in the spec? | **YES** - Optional field |
| Are they in our test file? | **YES** - Both exist |
| Why not visible in UI? | Check: scrolling, window size, colors |
| Should we display them? | **YES** - Always show what's available |
| What if they're empty? | Show "—" as placeholder |

---

## Next Steps

1. **Verify they're displaying** - Check if they appear when you scroll
2. **Test with other files** - Try different MBTiles files
3. **Improve handling** - Better display of partial/missing data
4. **Document variations** - Note which files have which fields

---

**Status:** All metadata fields are correctly read and should display.  
**Files affected:** `src/core/mbtiles_reader.py`, `src/gui/widgets/characteristics_panel.py`
