"""
MapLoom Main Window

Main application window with characteristics panel (left) and map panel (right).

Layout:
    [Characteristics Panel] | [Map Panel with Controls]
    - Left: Scrollable characteristics display with edit controls
    - Right: Interactive map viewer with zoom controls

Author: Development Team
Date: 2026-10-11
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSplitter, QMessageBox, QFileDialog, QMenu, QToolBar, QPushButton,
    QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon
import logging
from pathlib import Path
from typing import Optional
from src.core.mbtiles_reader import MBTilesReader
from src.core.zoom_generator import ZoomGenerator
from src.core.tile_processor import TileProcessor
from src.core.zoom_generation_worker import ZoomGenerationWorker
from src.map.mbtiles_provider import MBTilesProvider
from src.gui.widgets.characteristics_panel import CharacteristicsPanel
from src.gui.widgets.map_viewer import MapViewer
from src.gui.dialogs.zoom_selection_dialog import ZoomSelectionDialog
from src.gui.dialogs.zoom_generation_progress_dialog import ZoomGenerationProgressDialog
from config.app_config import AppConfig


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for MapLoom.
    
    Responsibilities:
        - Coordinate between characteristics panel and map viewer
        - Handle file loading and saving
        - Manage toolbar and menu actions
        - Manage layout and window state
    """
    
    # Signals
    file_loaded = pyqtSignal(str)  # Emitted when MBTiles file is loaded
    
    def __init__(self, parent=None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget (None for top-level window)
        """
        super().__init__(parent)
        
        self.current_file = None
        self.mbtiles_reader: Optional[MBTilesReader] = None
        self.config = AppConfig()  # Create config
        self.mbtiles_provider: Optional[MBTilesProvider] = None
        self.characteristics_panel: Optional[CharacteristicsPanel] = None
        self.map_viewer: Optional[MapViewer] = None
        
        # Setup window properties
        self.setWindowTitle("MapLoom - MBTiles Viewer and Zoom Level Generator")
        self.setWindowIcon(QIcon())  # TODO: Add application icon
        self.setGeometry(100, 100, 1400, 900)
        
        # Create MBTilesProvider (like CourseStudio does)
        self.mbtiles_provider = MBTilesProvider(config=self.config, logger=logger)
        
        # Initialize UI
        self._setup_ui()
        
        logger.info("MainWindow initialized")
    
    
    def _setup_ui(self):
        """
        Setup the user interface.
        
        Creates:
            - Menu bar with File, Edit, View, Help menus
            - Main splitter with characteristics and map panels
            - Toolbar with common actions
        """
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== MENU BAR =====
        self._create_menu_bar()
        
        # ===== TOOLBAR =====
        self._create_toolbar()
        
        # Create splitter for characteristics and map panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Characteristics panel (left)
        self.characteristics_panel = CharacteristicsPanel()
        
        # Map viewer panel (right) - Pass the provider like CourseStudio does!
        self.map_viewer = MapViewer()
        self.map_viewer.set_mbtiles_provider(self.mbtiles_provider)
        
        # Add panels to splitter
        splitter.addWidget(self.characteristics_panel)
        splitter.addWidget(self.map_viewer)
        
        # Set initial sizes - characteristics panel narrow, map wider
        # Use CourseStudio's approach: [left_width, right_width]
        splitter.setSizes([300, 700])
        
        # Allow panels to be resizable (stretch proportionally when window resizes)
        splitter.setStretchFactor(0, 1)  # Characteristics panel can expand/shrink
        splitter.setStretchFactor(1, 2)  # Map panel gets 2x more space by default
        
        # Don't prevent collapse - but you can if needed
        # splitter.setCollapsible(0, False)
        # splitter.setCollapsible(1, False)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # ===== STATUS BAR =====
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready - Open an MBTiles file to begin")
        
        logger.debug("UI setup complete")
    
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = file_menu.addAction("&Open MBTiles File")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file_dialog)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Tools menu (new)
        tools_menu = menubar.addMenu("&Tools")
        
        self.generate_zoom_action = tools_menu.addAction("&Generate Zoom Levels")
        self.generate_zoom_action.setShortcut("Ctrl+G")
        self.generate_zoom_action.triggered.connect(self.start_zoom_generation)
        self.generate_zoom_action.setEnabled(False)  # Disabled until file loaded
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)
        
        logger.debug("Menu bar created")
    
    
    def _create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Open file button
        open_button = QPushButton("📁 Open MBTiles File")
        open_button.clicked.connect(self.open_file_dialog)
        toolbar.addWidget(open_button)
        
        toolbar.addSeparator()
        
        # Generate zoom button (new)
        self.generate_button = QPushButton("⚙️ Generate Zoom Levels")
        self.generate_button.clicked.connect(self.start_zoom_generation)
        self.generate_button.setEnabled(False)  # Disabled until file loaded
        toolbar.addWidget(self.generate_button)
        
        toolbar.addSeparator()
        
        # Status label
        self.toolbar_status = QLabel("No file loaded")
        toolbar.addWidget(self.toolbar_status)
        
        logger.debug("Toolbar created")
    
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MapLoom",
            "MapLoom - MBTiles Viewer and Zoom Level Generator\n\n"
            "Version 0.1.0\n\n"
            "A desktop application for viewing MBTiles map files\n"
            "and generating missing zoom levels.\n\n"
            "Features:\n"
            "  • View MBTiles map characteristics\n"
            "  • Generate missing zoom levels\n"
            "  • Interpolation and downsampling\n"
            "  • Interactive map viewer\n\n"
            "Created: 2026-10-11"
        )

    
    
    def load_mbtiles_file(self, file_path: str) -> bool:
        """
        Load an MBTiles file.
        
        Args:
            file_path (str): Path to MBTiles file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"MBTiles file not found:\n{file_path}"
                )
                return False
            
            if path.suffix.lower() != '.mbtiles':
                logger.warning(f"Invalid file type: {file_path}")
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    f"File must have .mbtiles extension:\n{file_path}"
                )
                return False
            
            # Try to load the file
            logger.info(f"Loading MBTiles file: {file_path}")
            self.mbtiles_reader = MBTilesReader(file_path)
            
            # Update window
            self.current_file = file_path
            self.setWindowTitle(f"MapLoom - {path.name}")
            self.toolbar_status.setText(f"Loaded: {path.name}")
            self.statusBar.showMessage(f"Loaded: {file_path}")
            
            # Enable zoom generation button
            self.generate_button.setEnabled(True)
            self.generate_zoom_action.setEnabled(True)
            
            # Load characteristics panel
            if self.characteristics_panel:
                self.characteristics_panel.load_mbtiles(self.mbtiles_reader)
            
            # Load provider and map viewer
            if self.mbtiles_provider:
                # Load the file into provider
                success = self.mbtiles_provider.load_mbtiles_from_path(file_path)
                if success and self.map_viewer:
                    # Pass provider to map viewer (like CourseStudio does)
                    self.map_viewer.load_mbtiles(self.mbtiles_provider)
            
            logger.info(f"Successfully loaded MBTiles file: {file_path}")
            self.file_loaded.emit(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading file: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Failed to load MBTiles file:\n{str(e)}"
            )
            return False
    
    
    def open_file_dialog(self):
        """
        Open file browser dialog to select MBTiles file.
        """
        # Use last opened directory or mbtiles folder
        if self.current_file:
            default_dir = str(Path(self.current_file).parent)
        else:
            # Try MapLoom mbtiles folder first
            local_mbtiles = Path(__file__).parent.parent.parent / "mbtiles"
            if local_mbtiles.exists():
                default_dir = str(local_mbtiles)
            else:
                # Fall back to CourseStudio samples
                coursestudio_mbtiles = Path("/home/akoel/Projects/boat/general/Code/CourseStudio/mbtiles")
                if coursestudio_mbtiles.exists():
                    default_dir = str(coursestudio_mbtiles)
                else:
                    default_dir = str(Path.home())
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MBTiles File",
            default_dir,
            "MBTiles Files (*.mbtiles);;All Files (*)"
        )
        
        if file_path:
            logger.info(f"File dialog selected: {file_path}")
            self.load_mbtiles_file(file_path)
    
    
    def start_zoom_generation(self):
        """Start zoom level generation workflow."""
        if not self.mbtiles_reader:
            QMessageBox.warning(
                self,
                "No File Loaded",
                "Please open an MBTiles file first."
            )
            return
        
        # Step 1: Show zoom selection dialog
        generator = ZoomGenerator(self.mbtiles_reader)
        
        # Check if there are gaps to fill
        gaps = generator.analyze_gaps()
        if not gaps:
            QMessageBox.information(
                self,
                "No Missing Zooms",
                "This MBTiles file has no missing zoom levels.\n\n"
                "The following zooms are available:\n" +
                str(sorted(self.mbtiles_reader.get_available_zooms()))
            )
            return
        
        # Show zoom selection dialog
        selection_dialog = ZoomSelectionDialog(generator, self)
        if selection_dialog.exec_() != ZoomSelectionDialog.Accepted:
            return  # User cancelled
        
        selected_zooms = selection_dialog.get_selected_zooms()
        if not selected_zooms:
            return
        
        # Step 2: Generate selected zooms (in sequence)
        logger.info(f"Starting generation for zooms: {selected_zooms}")
        
        self.generator = generator
        self.selected_zooms = selected_zooms
        self.zoom_index = 0
        
        # Generate first zoom
        self._generate_next_zoom()
    
    
    def _generate_next_zoom(self):
        """Generate the next zoom in the sequence."""
        if self.zoom_index >= len(self.selected_zooms):
            # All zooms generated
            QMessageBox.information(
                self,
                "Generation Complete",
                f"Successfully generated {len(self.selected_zooms)} zoom levels."
            )
            
            # Refresh characteristics panel
            if self.characteristics_panel:
                self.characteristics_panel.load_mbtiles(self.mbtiles_reader)
            
            self.statusBar.showMessage("All zoom levels generated successfully")
            return
        
        target_zoom = self.selected_zooms[self.zoom_index]
        self.zoom_index += 1
        
        self._generate_single_zoom_threaded(target_zoom)
    
    
    def _generate_single_zoom_threaded(self, target_zoom):
        """
        Generate a single zoom level in background thread.
        
        Args:
            target_zoom: Zoom level to generate
        """
        try:
            # Create generation plan
            plan = self.generator.create_generation_plan(target_zoom)
            
            # Create processor
            processor = TileProcessor(self.mbtiles_reader, self.current_file)
            
            # Create progress dialog
            progress_dialog = ZoomGenerationProgressDialog(self, target_zoom, plan.tile_count)
            progress_dialog.start_generation(target_zoom, plan.tile_count)
            
            # Store dialog for later reference
            self.current_progress_dialog = progress_dialog
            
            # Create worker and thread
            worker = ZoomGenerationWorker(processor, plan, target_zoom)
            thread = QThread()
            worker.moveToThread(thread)
            
            # Connect signals
            worker.progress.connect(progress_dialog.update_progress)
            worker.finished.connect(lambda: self._on_generation_finished(thread, progress_dialog))
            worker.error.connect(lambda err: self._on_generation_error(thread, progress_dialog, err))
            worker.cancelled.connect(lambda: self._on_generation_cancelled(thread, progress_dialog))
            
            # Connect cancel button
            def on_cancel():
                worker.cancel()
            progress_dialog.cancel_button.clicked.disconnect()
            progress_dialog.cancel_button.clicked.connect(on_cancel)
            
            # Start thread
            thread.started.connect(worker.run)
            thread.start()
            
            # Store thread for cleanup
            self.generation_thread = thread
            self.generation_worker = worker
            
            # Show progress dialog (modal, but thread runs in background)
            progress_dialog.exec_()
        
        except Exception as e:
            logger.error(f"Error starting generation: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to start generation:\n{str(e)}"
            )
    
    
    def _on_generation_finished(self, thread, progress_dialog):
        """Handle successful generation completion."""
        logger.info("Generation finished successfully")
        progress_dialog.finish_success()
        
        # Stop thread
        thread.quit()
        thread.wait()
        
        # Update UI
        self.statusBar.showMessage(f"Successfully generated zoom level")
        
        # ✅ Mark the generated zoom level in the reader
        # This ensures the UI shows "Generated" instead of "Original"
        target_zoom = progress_dialog.target_zoom if hasattr(progress_dialog, 'target_zoom') else None
        if target_zoom and self.mbtiles_reader:
            self.mbtiles_reader.mark_zoom_as_generated(target_zoom)
            logger.info(f"Marked Z{target_zoom} as generated in reader")
        
        # ✅ Refresh reader's cached zoom levels from database
        if self.mbtiles_reader:
            self.mbtiles_reader.refresh_zoom_levels()
        
        # Refresh characteristics panel with updated zoom levels
        if self.characteristics_panel:
            self.characteristics_panel.load_mbtiles(self.mbtiles_reader)
        
        # Generate next zoom if any
        self._generate_next_zoom()
    
    
    def _on_generation_error(self, thread, progress_dialog, error_message):
        """Handle generation error."""
        logger.error(f"Generation error: {error_message}")
        progress_dialog.finish_error(error_message)
        
        # Stop thread
        thread.quit()
        thread.wait()
        
        # Show error (user can see full error in progress dialog)
        self.statusBar.showMessage(f"Error generating zoom level")
    
    
    def _on_generation_cancelled(self, thread, progress_dialog):
        """Handle user cancellation."""
        logger.info("Generation cancelled by user")
        progress_dialog.finish_cancelled()
        
        # Stop thread
        thread.quit()
        thread.wait()
        
        self.statusBar.showMessage("Generation cancelled")

    
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # TODO: Check for unsaved changes
        # TODO: Save window state (size, position)
        
        logger.info("MainWindow closing")
        event.accept()
