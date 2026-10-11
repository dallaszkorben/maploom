#!/usr/bin/env python3
"""
MapLoom - MBTiles Viewer and Zoom Level Generator

Main entry point for the MapLoom application.
Initializes the application and launches the PyQt5 GUI.

Features:
    - Read and display MBTiles map files
    - Show file characteristics (name, description, format, zooms, center)
    - Modify zoom levels (generate missing zoom levels via interpolation)
    - Visual left panel for characteristics, right panel for map
    - Progress indicator for zoom generation with cancel option

Usage:
    python src/main.py [--file path/to/file.mbtiles]

Author: Development Team
Date: 2026-10-11
"""

import sys
import argparse
import logging
import traceback
from pathlib import Path

# Add project root to path so imports work correctly
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMessageBox


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(debug: bool = False):
    """
    Configure logging for the application.
    
    Args:
        debug (bool): Enable debug level logging
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(project_root / 'maploom.log')
        ]
    )


# ============================================================================
# Application Entry Point
# ============================================================================

def main():
    """
    Main application entry point.
    
    Parses command-line arguments, initializes PyQt5 application,
    and launches the main window.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='MapLoom - MBTiles Viewer and Zoom Level Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                          # Open with file browser
  python src/main.py --file map.mbtiles       # Open specific file
  python src/main.py --debug                  # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Path to MBTiles file to open on startup'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug level logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='MapLoom 0.1.0'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("MapLoom Application Starting")
    logger.info("=" * 70)
    
    try:
        # Import GUI after logging is set up
        from src.gui.main_window import MainWindow
        
        # Create PyQt5 application
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Load file if specified
        if args.file:
            mbtiles_path = Path(args.file)
            if mbtiles_path.exists():
                logger.info(f"Loading MBTiles file: {mbtiles_path}")
                window.load_mbtiles_file(str(mbtiles_path))
            else:
                logger.warning(f"File not found: {mbtiles_path}")
                QMessageBox.warning(
                    window,
                    "File Not Found",
                    f"Could not find MBTiles file:\n{mbtiles_path}"
                )
        
        logger.info("Application GUI initialized and displayed")
        
        # Run application event loop
        exit_code = app.exec_()
        logger.info(f"Application exiting with code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error during application startup: {e}")
        logger.error(traceback.format_exc())
        
        # Show error dialog even if app creation failed
        try:
            QMessageBox.critical(
                None,
                "Application Error",
                f"Failed to start MapLoom:\n\n{str(e)}\n\nCheck maploom.log for details."
            )
        except Exception:
            print(f"FATAL ERROR: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
