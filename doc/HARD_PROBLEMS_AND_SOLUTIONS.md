# Hard Problems and Solutions

**Document:** Recording complex issues discovered during development and their solutions  
**Date:** 2026-10-11  
**Status:** Active problem tracking

---

## Problem 1: Incomplete Zoom Generation Creates Orphaned Tiles

### Issue Description

**Date Discovered:** 2026-10-11  
**Severity:** High  
**Status:** FIXED ✅

When zoom level generation is interrupted (user cancels or app crashes), partially-generated tiles remain in the MBTiles database. Upon reopening the file, these incomplete zooms appear to the user, creating data inconsistency.

### Root Cause

The original implementation wrote tiles incrementally to the database as they were generated:

```python
for tile_x in range(2 ** target_zoom):
    for tile_y in range(2 ** target_zoom):
        tile_data = generate_tile(...)
        write_tile(...)  # ❌ Writes immediately to real database
```

If interrupted at any point:
- Some tiles already in database
- Some tiles not yet generated
- No way to know which is which
- Incomplete zoom appears as valid

### Failed Attempts

**Attempt 1: Delete tiles on cancel**
```python
if user_cancelled:
    delete_all_tiles_for_zoom(zoom)
```
Problem: Doesn't help if app crashes - tiles stay in DB

**Attempt 2: Store all in memory**
```python
tiles = []
for tile_x, tile_y:
    tile_data = generate_tile(...)
    tiles.append((tile_x, tile_y, tile_data))
write_all_tiles(tiles)
```
Problem: Out-of-memory errors for large zoom levels (Z12+ can exceed available RAM)

### Final Solution: Temporary Database with Atomic Commit

**Strategy:**
1. Generate tiles into a **temporary SQLite database** (separate file)
2. Verify generation is complete (count tiles, spot-check content)
3. Once verified, **atomically copy all tiles** to real database in single transaction
4. Delete temporary database

**Why it works:**
- ✅ No memory issues (tiles written to disk incrementally)
- ✅ Real database never touched during generation
- ✅ If app crashes → temp file orphaned but real DB untouched
- ✅ If cancelled → temp file deleted, no traces in real DB
- ✅ Atomic final operation (either all tiles appear or none)

**Implementation:**

```python
class TileProcessor:
    def __init__(self, reader, filepath, temp_dir=None):
        self.reader = reader
        self.filepath = filepath
        self.temp_dir = temp_dir or Path(filepath).parent / ".maploom_temp"
        self.temp_db_path = None
    
    def generate_tiles_to_temp(self, source_zoom, target_zoom):
        """Generate tiles to temporary database."""
        # Create temp DB
        self.temp_db_path = self.temp_dir / f"gen_z{target_zoom}_{int(time.time())}.db"
        self.temp_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate tiles into temp DB
        for tile_x, tile_y in tile_iterator(target_zoom):
            tile_data = self.generate_tile(source_zoom, target_zoom, tile_x, tile_y)
            self._write_to_temp_db(target_zoom, tile_x, tile_y, tile_data)
        
        # Verify completion
        if not self._verify_generation_complete(target_zoom):
            raise GenerationError("Generation incomplete or corrupted")
        
        return self.temp_db_path
    
    def commit_generated_tiles(self, temp_db_path, target_zoom):
        """Atomically move tiles from temp DB to real DB."""
        try:
            # Begin transaction on real database
            conn = sqlite3.connect(self.filepath)
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            # Copy all tiles from temp to real database
            temp_conn = sqlite3.connect(temp_db_path)
            temp_cursor = temp_conn.cursor()
            
            tiles = temp_cursor.execute(
                "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
            ).fetchall()
            
            insert_sql = """
                INSERT OR IGNORE INTO tiles 
                (zoom_level, tile_column, tile_row, tile_data)
                VALUES (?, ?, ?, ?)
            """
            cursor.executemany(insert_sql, tiles)
            
            # Mark zoom as generated
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                (f"generated_zoom_{target_zoom}", "true")
            )
            
            # Commit atomic transaction
            cursor.execute("COMMIT")
            conn.close()
            temp_conn.close()
            
            # Clean up temp database
            temp_db_path.unlink()
            
        except Exception as e:
            # Rollback if anything fails
            if conn:
                cursor.execute("ROLLBACK")
                conn.close()
            raise GenerationError(f"Failed to commit tiles: {e}")
```

### Key Insights

1. **Atomicity is crucial** - Either all tiles written or none
2. **Disk temporary storage** - Avoids memory issues with large zooms
3. **Verification step** - Catches incomplete generations
4. **Clean separation** - Real DB only touched when everything is verified

### Testing

- ✅ Normal generation completes and commits
- ✅ Cancellation leaves no traces in real DB
- ✅ App crash leaves temp file but real DB intact
- ✅ Large zoom levels don't cause OOM errors
- ✅ Multiple simultaneous generations possible (each has unique temp file)

---

## Problem 2: Tile Count Math Inconsistency

### Issue Description

**Date Discovered:** 2026-10-11  
**Severity:** Medium  
**Status:** FIXED ✅

Generated incomplete zoom levels showed incorrect tile counts. Example:
- Z8: 600 tiles (should be 0 if not fully generated)
- Z9 (cancelled): 18,282 tiles (incomplete, should be 0 or 262,144)
- Z10: 2,560 tiles (should be 0 if not fully generated)

### Root Cause

With incremental writes, partial zooms accumulate tiles until cancellation. The count reflects how many tiles were written before interruption, not the actual theoretical count.

### Why This Matters

Users see incomplete zooms with arbitrary tile counts, suggesting they're valid but partial. Creates data integrity confusion.

### Solution

With the temporary database approach:
- ✅ If generation completes: zoom appears with exact expected tile count (4^z tiles)
- ✅ If generation cancelled: zoom doesn't appear at all
- ✅ No intermediate states with weird tile counts

**Verification logic:**

```python
def _verify_generation_complete(self, target_zoom):
    """Verify all tiles were generated."""
    expected_tiles = 4 ** target_zoom
    
    cursor = sqlite3.connect(self.temp_db_path).cursor()
    actual_tiles = cursor.execute(
        "SELECT COUNT(*) FROM tiles WHERE zoom_level = ?",
        (target_zoom,)
    ).fetchone()[0]
    
    if actual_tiles != expected_tiles:
        logger.error(f"Generation incomplete: {actual_tiles}/{expected_tiles} tiles")
        return False
    
    return True
```

### Key Insight

**Clean atomicity prevents dirty states.** Either a zoom is completely generated with correct tile count, or it doesn't exist at all.

---

## Problem 3: Generated Zoom Tiles Display with Vertical Stripe Misalignment

### Issue Description

**Date Discovered:** 2026-10-11  
**Severity:** Critical  
**Status:** FIXED ✅

Generated Z9 tiles appeared to have horizontally-scrambled vertical stripes. The map showed:
- Horizontal stripes that didn't align with each other vertically
- "Every second stripe belongs together but in opposite order"
- Vertical misalignment only; horizontal alignment was correct
- Original Z10 tiles displayed correctly

### Investigation Process

**Initial Hypothesis:** Downsampling algorithm has Y-axis inversion bug
- Tried reversing row order during composition
- Tried flipping tiles vertically
- Tried swapping row/column interpretation
- **All attempts failed** - same visual issue

**Key Observation:** Z9 tile pixel analysis showed:
```
Z9 quadrant colors EXACTLY matched Z10 source tiles
=> Downsampling was working correctly!
```

**Breakthrough:** Examined edge continuity of ORIGINAL Z10 tiles:
```
Adjacent Z10 rows (696→697) had discontinuous edges:
  Diff: 6161 (very different)
But reversed interpretation (697 bottom→696 top):
  Diff: 333 (much better!)
```

This seemed to suggest Z10 was stored upside-down. But wait... Z10 displayed correctly!

**Final Insight:** Checked the tile viewer's coordinate conversion:

```python
# From mbtiles_provider.py get_tile():
max_tile_y = (2 ** zoom) - 1
tms_y = max_tile_y - y  # ← TMS conversion formula
```

The viewer applies TMS Y-axis inversion when displaying tiles!

### Root Cause

**Two-part problem:**

1. **The viewer applies TMS conversion** - It inverts the Y-axis for display:
   ```
   tms_y = (2^zoom - 1) - y
   ```

2. **Generated tiles weren't compensated** - When downsampling Z10→Z9:
   - Z10 tiles stored in database get inverted by viewer
   - Z9 tiles also get inverted by viewer
   - But Z9 is composed from Z10 tiles in normal order
   - Result: Z9 quadrants are in wrong positions after inversion!

### Why Initial Debugging Failed

- Focused on downsampling code (which was correct!)
- Didn't realize the viewer was applying transformations
- Tile pixel data matched source (composition was working!)
- The misalignment happened at DISPLAY time, not generation time

### Solution: Compensate During Downsampling

Instead of trying to fix the viewer's conversion (which is correct for other MBTiles files), **compensate during downsampling** by swapping quadrant positions:

**Normal downsampling:**
```
Z10 sources                Canvas placement
(col*2, row*2)      →      (0, 0)     [TOP-LEFT]
(col*2+1, row*2)    →      (256, 0)   [TOP-RIGHT]
(col*2, row*2+1)    →      (0, 256)   [BOTTOM-LEFT]
(col*2+1, row*2+1)  →      (256, 256) [BOTTOM-RIGHT]
```

**Compensated downsampling:**
```
Z10 sources                Canvas placement (SWAPPED)
(col*2, row*2)      →      (0, 256)   [BOTTOM-LEFT] ← swapped
(col*2+1, row*2)    →      (256, 256) [BOTTOM-RIGHT]← swapped
(col*2, row*2+1)    →      (0, 0)     [TOP-LEFT]    ← swapped
(col*2+1, row*2+1)  →      (256, 0)   [TOP-RIGHT]   ← swapped
```

**Why this works:**
1. Z9 tile is composed with top/bottom swapped
2. Viewer later applies TMS inversion (top↔bottom)
3. Inversion cancels the swap: correct positions!

**Implementation:**

```python
# In tile_processor.py downsample_tile()
source_tiles_db = [
    (target_column * 2,     target_row * 2),
    (target_column * 2 + 1, target_row * 2),
    (target_column * 2,     target_row * 2 + 1),
    (target_column * 2 + 1, target_row * 2 + 1)
]

# SWAP top and bottom to compensate for viewer's TMS conversion
canvas_positions = [
    (0, 256),      # Bottom-left (will become top after inversion)
    (256, 256),    # Bottom-right
    (0, 0),        # Top-left (will become bottom after inversion)
    (256, 0)       # Top-right
]

for i, (src_col, src_row) in enumerate(source_tiles_db):
    tile_image = fetch_tile(source_zoom, src_col, src_row)
    canvas.paste(tile_image, canvas_positions[i])
```

### Key Insights

1. **Coordinate systems matter** - Viewer and database don't necessarily use same convention
2. **Composition happens before display** - Fix at generation time, not display time
3. **Symmetry is powerful** - Swapping top/bottom twice returns to original
4. **Test with actual display** - Pixel data analysis alone wasn't enough

### Why Z10 Displayed Correctly

- Z10 tiles in database are already "correct" for the viewer's inversion
- Viewer inverts them, and they display correctly
- No composition happening (they're original, not generated)

### Why Z9 Initially Looked Wrong

- Z9 composed from Z10 in standard order
- Viewer inverted Z9 tiles
- But inversion happened on already-composed (and inverted) quadrants
- Result: double inversion created misalignment

### Testing

- ✅ Z9 tiles now display with correct vertical alignment
- ✅ Horizontal stripes align properly
- ✅ Geographic accuracy maintained
- ✅ Z10 original tiles still display correctly
- ✅ Both Z8 and Z9 show seamless tile boundaries

### Generalization

**This is specific to this OSM-OpenCPN2-Baltic MBTiles file**, which uses a coordinate system that the viewer's conversion handles correctly for original tiles but not for generated tiles.

If using other MBTiles files:
- Test with original zooms first (should display correctly)
- If they display correctly, use this compensation
- If they display upside-down, may need different approach

---

## Lessons Learned

### Lessons Learned from All Problems

1. **Database Atomicity is Critical** - Never write production data incrementally
2. **Coordinate Systems Matter** - Understand where conversions happen
3. **Fix at the Right Layer** - Downsampling algorithm wasn't the problem; viewer's conversion was
4. **Test Complete Pipeline** - Pixel data can be correct but display wrong due to transformations
5. **Keep Detailed Diagnostics** - Comparing pixel values helped identify real issue

---

## Implementation Status

| Problem | Status | Impact | Solution |
|---------|--------|--------|----------|
| Incomplete zoom orphans | ✅ FIXED | Prevents data corruption | Temp DB + atomic commit |
| Tile count math | ✅ FIXED | Clean state tracking | Verification before commit |
| Z9 vertical misalignment | ✅ FIXED | Correct map display | Compensate for viewer's TMS conversion |

---

**Document maintained by:** Development Team  
**Last updated:** 2026-10-11
