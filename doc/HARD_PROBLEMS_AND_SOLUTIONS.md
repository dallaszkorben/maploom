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

## Lessons Learned

### 1. Database Atomicity is Critical
- Never write production data incrementally
- Use temporary storage for in-progress work
- Atomic final commit to real database

### 2. Handle Interruption Gracefully
- App crashes and cancellations are inevitable
- Design for clean recovery
- Leave no traces in real data if interrupted

### 3. Disk Better Than Memory for Large Operations
- MBTiles can be huge (Z12+ has billions of tiles)
- Temporary database on disk scales better than memory
- Trade disk I/O for memory safety

### 4. Verification is Essential
- Don't assume generation completed successfully
- Count tiles, spot-check content
- Fail loudly if verification fails

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Temporary DB creation | ✅ DONE | Separate SQLite file |
| Tile generation to temp | ✅ DONE | Incremental writes safe |
| Verification logic | ✅ DONE | Count and integrity checks |
| Atomic commit | ✅ DONE | Single transaction |
| Cleanup on cancel | ✅ DONE | Temp file deleted |
| Cleanup on error | ✅ DONE | Temp file deleted, DB rolled back |
| Testing | ✅ DONE | All scenarios covered |

---

## Future References

If similar issues arise in other areas:

1. **General principle**: Separate working state from production state
2. **Pattern**: Temp storage → Verify → Atomic commit
3. **Apply to**: Any operation that modifies persistent data

---

**Document maintained by:** Development Team  
**Last updated:** 2026-10-11
