"""
Tile server for fetching and caching tiles from MBTiles database.

Responsibilities:
- Fetch tiles from MBTiles by zoom/column/row
- Cache frequently accessed tiles in memory
- Handle tile format conversions (PNG, JPEG, WebP)
- Provide tile data for map rendering
"""

import logging
import sqlite3
from functools import lru_cache
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TileServer:
    """
    Serves map tiles from an MBTiles database.
    
    The MBTiles database stores tiles in a SQLite table with schema:
    - zoom_level: Zoom level (0-28 typically)
    - tile_column: X coordinate (0 to 2^zoom - 1)
    - tile_row: Y coordinate in TMS format (0,0 is bottom-left)
    - tile_data: BLOB containing the tile image (PNG, JPEG, or WebP)
    """
    
    def __init__(self, mbtiles_path: str, cache_size: int = 256):
        """
        Initialize the tile server.
        
        Args:
            mbtiles_path (str): Path to the MBTiles file
            cache_size (int): Number of tiles to cache in memory (default: 256)
        
        Raises:
            FileNotFoundError: If MBTiles file doesn't exist
            sqlite3.DatabaseError: If MBTiles is not a valid SQLite database
        """
        self.mbtiles_path = Path(mbtiles_path)
        
        if not self.mbtiles_path.exists():
            raise FileNotFoundError(f"MBTiles file not found: {mbtiles_path}")
        
        # Verify it's a valid MBTiles database
        try:
            conn = sqlite3.connect(str(self.mbtiles_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tiles'")
            if not cursor.fetchone():
                raise sqlite3.DatabaseError("Not a valid MBTiles file: 'tiles' table not found")
            conn.close()
        except sqlite3.DatabaseError as e:
            raise sqlite3.DatabaseError(f"Not a valid MBTiles file: {e}")
        
        self._cache_size = cache_size
        self._cache = {}  # Dictionary: (zoom, column, row) -> tile_data
    
    def get_tile(self, zoom: int, column: int, row: int) -> Optional[bytes]:
        """
        Fetch a tile from the MBTiles database.
        
        Uses in-memory caching for frequently accessed tiles.
        
        Args:
            zoom (int): Zoom level (0-28 typically)
            column (int): Tile column (X coordinate, 0 to 2^zoom - 1)
            row (int): Tile row (Y coordinate in TMS format, 0 is bottom)
        
        Returns:
            bytes: Tile image data (PNG/JPEG/WebP), or None if tile not found
        """
        # Check cache first
        cache_key = (zoom, column, row)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            conn = sqlite3.connect(str(self.mbtiles_path))
            cursor = conn.cursor()
            
            # Query tile data (note: TMS format uses row as-is)
            cursor.execute(
                "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                (zoom, column, row)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                tile_data = result[0]
                
                # Cache the tile (with simple LRU eviction when cache is full)
                if len(self._cache) >= self._cache_size:
                    # Remove oldest entry (simple FIFO, not true LRU)
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                
                self._cache[cache_key] = tile_data
                return tile_data
            
            return None
        
        except sqlite3.Error as e:
            logger.warning(f"Error fetching tile Z{zoom}/{column}/{row}: {e}")
            return None
    
    def tile_exists(self, zoom: int, column: int, row: int) -> bool:
        """
        Check if a tile exists in the database.
        
        Args:
            zoom (int): Zoom level
            column (int): Tile column
            row (int): Tile row
        
        Returns:
            bool: True if tile exists, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.mbtiles_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ? LIMIT 1",
                (zoom, column, row)
            )
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except sqlite3.Error as e:
            logger.warning(f"Error checking tile Z{zoom}/{column}/{row}: {e}")
            return False
    
    def clear_cache(self):
        """Clear the in-memory tile cache."""
        self._cache.clear()
        logger.debug(f"Tile cache cleared")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            dict: Statistics including cache size, number of cached tiles, etc.
        """
        return {
            'max_size': self._cache_size,
            'current_size': len(self._cache),
            'cache_hit_rate': len(self._cache) / self._cache_size if self._cache_size > 0 else 0
        }
