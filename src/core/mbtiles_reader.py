"""
MBTiles File Reader

Reads and parses MBTiles SQLite database files.
Extracts metadata, zoom levels, and file statistics.

MBTiles Specification:
- SQLite 3 database with metadata and tiles tables
- metadata table: key-value pairs (name, description, format, etc.)
- tiles table: (zoom_level, tile_column, tile_row, tile_data) BLOB storage

Author: Development Team
Date: 2026-10-11
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class MBTilesMetadata:
    """Container for MBTiles metadata."""
    
    name: str = "Unknown"
    description: str = ""
    format: str = "unknown"
    version: str = "1.1"
    type: str = "baselayer"
    bounds: Optional[Tuple[float, float, float, float]] = None  # west, south, east, north
    center: Optional[Tuple[float, float, int]] = None  # lon, lat, zoom
    minzoom: int = 0
    maxzoom: int = 28
    attribution: str = ""
    
    def __str__(self) -> str:
        """String representation of metadata."""
        return (
            f"Name: {self.name}\n"
            f"Description: {self.description}\n"
            f"Format: {self.format}\n"
            f"Version: {self.version}\n"
            f"Type: {self.type}\n"
            f"Zoom Range: Z{self.minzoom}-Z{self.maxzoom}\n"
            f"Bounds: {self.bounds}\n"
            f"Center: {self.center}"
        )


@dataclass
class ZoomLevelInfo:
    """Information about a zoom level."""
    
    zoom: int
    tile_count: int
    is_original: bool = True  # True if from original file, False if generated


class MBTilesReader:
    """
    Reader for MBTiles files.
    
    Responsibilities:
        - Open and validate MBTiles files
        - Extract metadata
        - List available zoom levels
        - Calculate file statistics
        - Track generated vs original zoom levels
    """
    
    def __init__(self, file_path: str):
        """
        Initialize MBTiles reader.
        
        Args:
            file_path (str): Path to .mbtiles file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid MBTiles format
        """
        self.file_path = Path(file_path)
        self.metadata: Optional[MBTilesMetadata] = None
        self.zoom_levels: List[ZoomLevelInfo] = []
        self._generated_zooms: set = set()  # Track which zooms were generated
        
        self._validate_file()
        self._load_metadata()
        self._load_zoom_levels()
        
        logger.info(f"Loaded MBTiles file: {self.file_path}")
    
    
    def _validate_file(self) -> None:
        """
        Validate that file is a valid MBTiles database.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid MBTiles
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"MBTiles file not found: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.mbtiles':
            logger.warning(f"File doesn't have .mbtiles extension: {self.file_path}")
        
        # Try to open as SQLite database and check for required tables
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()
            
            # Check for metadata table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
            )
            if not cursor.fetchone():
                raise ValueError("Missing metadata table")
            
            # Check for tiles table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tiles'"
            )
            if not cursor.fetchone():
                raise ValueError("Missing tiles table")
            
            conn.close()
            logger.debug(f"Validated MBTiles structure for: {self.file_path}")
            
        except sqlite3.DatabaseError as e:
            raise ValueError(f"Not a valid SQLite database: {e}")
    
    
    def _load_metadata(self) -> None:
        """Load metadata from the MBTiles file."""
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()
            
            # Get all metadata
            cursor.execute("SELECT name, value FROM metadata")
            metadata_dict = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            # Parse metadata
            self.metadata = MBTilesMetadata()
            self.metadata.name = metadata_dict.get('name', 'Unknown')
            self.metadata.description = metadata_dict.get('description', '')
            self.metadata.format = metadata_dict.get('format', 'unknown')
            self.metadata.version = metadata_dict.get('version', '1.1')
            self.metadata.type = metadata_dict.get('type', 'baselayer')
            self.metadata.attribution = metadata_dict.get('attribution', '')
            
            # Parse minzoom/maxzoom
            try:
                self.metadata.minzoom = int(metadata_dict.get('minzoom', 0))
                self.metadata.maxzoom = int(metadata_dict.get('maxzoom', 28))
            except (ValueError, TypeError):
                self.metadata.minzoom = 0
                self.metadata.maxzoom = 28
            
            # Parse bounds: "west,south,east,north"
            bounds_str = metadata_dict.get('bounds', '')
            if bounds_str:
                try:
                    parts = [float(x.strip()) for x in bounds_str.split(',')]
                    if len(parts) == 4:
                        self.metadata.bounds = tuple(parts)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse bounds: {bounds_str}")
            
            # Parse center: "lon,lat,zoom"
            center_str = metadata_dict.get('center', '')
            if center_str:
                try:
                    parts = center_str.split(',')
                    if len(parts) >= 2:
                        lon = float(parts[0].strip())
                        lat = float(parts[1].strip())
                        zoom = int(parts[2].strip()) if len(parts) >= 3 else 0
                        self.metadata.center = (lon, lat, zoom)
                except (ValueError, TypeError, IndexError):
                    logger.warning(f"Could not parse center: {center_str}")
            
            logger.debug(f"Loaded metadata: {self.metadata.name}")
            
        except Exception as e:
            logger.error(f"Error loading metadata: {e}", exc_info=True)
            self.metadata = MBTilesMetadata()
    
    
    def _load_zoom_levels(self) -> None:
        """Load available zoom levels from tiles table."""
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()
            
            # Get all zoom levels and count tiles per level
            cursor.execute(
                "SELECT zoom_level, COUNT(*) as tile_count "
                "FROM tiles "
                "GROUP BY zoom_level "
                "ORDER BY zoom_level ASC"
            )
            
            self.zoom_levels = []
            for zoom, tile_count in cursor.fetchall():
                is_original = zoom not in self._generated_zooms
                self.zoom_levels.append(
                    ZoomLevelInfo(
                        zoom=zoom,
                        tile_count=tile_count,
                        is_original=is_original
                    )
                )
            
            conn.close()
            logger.debug(f"Found {len(self.zoom_levels)} zoom levels")
            
        except Exception as e:
            logger.error(f"Error loading zoom levels: {e}", exc_info=True)
            self.zoom_levels = []
    
    
    def get_metadata(self) -> MBTilesMetadata:
        """
        Get file metadata.
        
        Returns:
            MBTilesMetadata: File metadata
        """
        return self.metadata or MBTilesMetadata()
    
    
    def get_zoom_levels(self) -> List[ZoomLevelInfo]:
        """
        Get list of available zoom levels.
        
        Returns:
            List[ZoomLevelInfo]: Zoom levels sorted by zoom value
        """
        return sorted(self.zoom_levels, key=lambda z: z.zoom)
    
    
    def get_available_zooms(self) -> List[int]:
        """
        Get list of available zoom level numbers.
        
        Returns:
            List[int]: Zoom numbers (e.g., [8, 10, 12, 14, 16])
        """
        return sorted([z.zoom for z in self.zoom_levels])
    
    
    def get_missing_zooms(self) -> List[int]:
        """
        Get list of missing zoom levels in the continuous range.
        
        For example, if available is [8, 10, 12, 14, 16], returns [9, 11, 13, 15]
        
        Returns:
            List[int]: Missing zoom numbers
        """
        if not self.zoom_levels:
            return []
        
        available = self.get_available_zooms()
        min_zoom = min(available)
        max_zoom = max(available)
        
        missing = []
        for z in range(min_zoom, max_zoom + 1):
            if z not in available:
                missing.append(z)
        
        return missing
    
    
    def get_file_statistics(self) -> Dict[str, any]:
        """
        Get file statistics.
        
        Returns:
            Dict with keys:
                - file_size: Size in bytes
                - total_tiles: Total tiles across all zooms
                - zoom_count: Number of zoom levels
                - zoom_range: (min_zoom, max_zoom)
        """
        total_tiles = sum(z.tile_count for z in self.zoom_levels)
        file_size = self.file_path.stat().st_size
        zoom_range = (
            min(z.zoom for z in self.zoom_levels) if self.zoom_levels else 0,
            max(z.zoom for z in self.zoom_levels) if self.zoom_levels else 0
        )
        
        return {
            'file_size': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'total_tiles': total_tiles,
            'zoom_count': len(self.zoom_levels),
            'zoom_range': zoom_range,
            'original_zoom_count': sum(1 for z in self.zoom_levels if z.is_original),
            'generated_zoom_count': sum(1 for z in self.zoom_levels if not z.is_original),
        }
    
    
    def get_tile(self, zoom: int, x: int, y: int) -> Optional[bytes]:
        """
        Get a tile blob from the database.
        
        Args:
            zoom (int): Zoom level
            x (int): Tile column (X coordinate)
            y (int): Tile row (Y coordinate in TMS format)
            
        Returns:
            bytes: Tile data, or None if not found
        """
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                (zoom, x, y)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Error reading tile Z{zoom}/{x}/{y}: {e}")
            return None
    
    
    def mark_zoom_as_generated(self, zoom: int) -> None:
        """
        Mark a zoom level as generated (not original).
        
        Args:
            zoom (int): Zoom level to mark
        """
        self._generated_zooms.add(zoom)
        
        # Update zoom level info
        for z in self.zoom_levels:
            if z.zoom == zoom:
                z.is_original = False
                break
        
        logger.debug(f"Marked zoom {zoom} as generated")
    
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MBTilesReader({self.file_path.name}, "
            f"zooms={self.get_available_zooms()}, "
            f"tiles={sum(z.tile_count for z in self.zoom_levels)})"
        )
