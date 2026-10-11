"""Minimal configuration class for MapLoom."""


class AppConfig:
    """Minimal configuration for MapLoom - compatible with MBTilesProvider."""
    
    def __init__(self):
        """Initialize with default values."""
        self.values = {
            'Appearance.Tiles.recent_center.lat': None,
            'Appearance.Tiles.recent_center.lon': None,
            'Appearance.Tiles.default_center.lat': 0,
            'Appearance.Tiles.default_center.lon': 0,
            'Appearance.Tiles.default_zoom': 10,
            'Appearance.Tiles.recent_zoom': None,
            'Appearance.MapDisplay.TrackPath.body.color': 'FF0000',
            'Appearance.MapDisplay.TrackPath.body.width': 3,
            'Appearance.MapDisplay.TrackPath.outline.color': 'FFFFFF',
            'Appearance.MapDisplay.TrackPath.outline.width': 1,
            'Appearance.MapDisplay.Trackpoints.show': True,
            'Appearance.MapDisplay.Trackpoints.GeneralPoints.body.color': 'FFFF00',
            'Appearance.MapDisplay.Trackpoints.GeneralPoints.body.size': 4,
            'Appearance.MapDisplay.Trackpoints.GeneralPoints.outline.color': 'FFFFFF',
            'Appearance.MapDisplay.Trackpoints.GeneralPoints.outline.size': 1,
            'Appearance.MapDisplay.Trackpoints.SelectedPoints.body.color': '0000FF',
            'Appearance.MapDisplay.Trackpoints.SelectedPoints.body.size': 7,
            'Appearance.MapDisplay.Trackpoints.SelectedPoints.outline.color': 'FFFFFF',
            'Appearance.MapDisplay.Trackpoints.SelectedPoints.outline.size': 2,
        }
    
    def get_str(self, key: str, default: str = '') -> str:
        """Get string configuration value."""
        return str(self.values.get(key, default))
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        val = self.values.get(key, default)
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        val = self.values.get(key, default)
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        val = self.values.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)
