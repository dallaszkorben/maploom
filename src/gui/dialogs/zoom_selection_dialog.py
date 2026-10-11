"""
Zoom Selection Dialog - Let user choose which zoom levels to generate.

Shows:
- Available zoom levels
- Missing zoom levels (checkbox list)
- Quality warnings for risky selections
- Preview of what will happen
- Confirmation button

Usage:
    >>> dialog = ZoomSelectionDialog(generator, parent)
    >>> if dialog.exec_() == QDialog.Accepted:
    ...     selected_zooms = dialog.get_selected_zooms()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QScrollArea,
    QPushButton, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class ZoomSelectionDialog(QDialog):
    """
    Dialog for selecting which zoom levels to generate.
    
    Allows user to:
    - See available and missing zoom levels
    - Select which missing levels to generate
    - See quality warnings for risky selections
    - Preview generation plans
    """
    
    def __init__(self, generator, parent=None):
        """
        Initialize zoom selection dialog.
        
        Args:
            generator: ZoomGenerator instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.generator = generator
        self.selected_zooms = []
        self.checkboxes = {}
        
        self._setup_ui()
        self._populate_zoom_levels()
    
    def _setup_ui(self):
        """Create and layout UI components."""
        self.setWindowTitle("Generate Missing Zoom Levels")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        # Title
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title = QLabel("Select Zoom Levels to Generate")
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Summary info
        summary = QLabel()
        try:
            summary_text = self.generator.get_summary()
            summary.setText(summary_text)
        except Exception as e:
            summary.setText(f"Error: {e}")
        layout.addWidget(summary)
        
        # Zoom levels selection (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Get missing zooms
        try:
            missing_zooms = self.generator.analyze_gaps()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to analyze gaps: {e}")
            missing_zooms = []
        
        if missing_zooms:
            title_label = QLabel("Missing Zoom Levels (select to generate):")
            title_label_font = QFont()
            title_label_font.setBold(True)
            title_label.setFont(title_label_font)
            scroll_layout.addWidget(title_label)
            
            for zoom in missing_zooms:
                # Create checkbox for each missing zoom
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout()
                
                checkbox = QCheckBox(f"Z{zoom}")
                checkbox.zoom_level = zoom
                checkbox.stateChanged.connect(self._on_zoom_selected)
                self.checkboxes[zoom] = checkbox
                
                # Try to create plan to show info/warnings
                try:
                    plan = self.generator.create_generation_plan(zoom)
                    info_text = f" ({plan.source_type}, {plan.tile_count:,} tiles"
                    
                    if plan.quality_warning:
                        info_text += f" ⚠️)"
                    else:
                        info_text += ")"
                    
                    info_label = QLabel(info_text)
                    if plan.quality_warning:
                        info_label.setToolTip(plan.quality_reason)
                    
                except Exception as e:
                    info_label = QLabel(f" (Error: {e})")
                
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.addWidget(info_label)
                checkbox_layout.addStretch()
                checkbox_widget.setLayout(checkbox_layout)
                
                scroll_layout.addWidget(checkbox_widget)
        else:
            no_gaps_label = QLabel("No missing zoom levels detected!")
            scroll_layout.addWidget(no_gaps_label)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Info text
        info_text = QLabel(
            "⚠️ = Quality warning\n\n"
            "Select the zoom levels you want to generate and click OK.\n"
            "Generation may take several minutes depending on zoom level."
        )
        layout.addWidget(info_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("Generate Selected")
        ok_button.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _populate_zoom_levels(self):
        """Populate zoom levels from generator."""
        pass  # Already done in _setup_ui
    
    def _on_zoom_selected(self, state):
        """Handle zoom level selection change."""
        pass  # Just track, validate on OK
    
    def _on_ok(self):
        """Handle OK button click."""
        # Get selected zooms
        self.selected_zooms = [
            zoom for zoom, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]
        
        if not self.selected_zooms:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one zoom level to generate."
            )
            return
        
        # Show confirmation dialog with quality warnings
        warning_text = ""
        for zoom in sorted(self.selected_zooms):
            try:
                plan = self.generator.create_generation_plan(zoom)
                if plan.quality_warning:
                    warning_text += f"• Z{zoom}: {plan.quality_reason}\n"
            except Exception:
                pass
        
        if warning_text:
            confirm = QMessageBox.warning(
                self,
                "Quality Warnings",
                f"⚠️ The following zooms have quality concerns:\n\n{warning_text}\n"
                "Do you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
        
        # Accept dialog
        self.accept()
    
    def get_selected_zooms(self):
        """
        Get list of selected zoom levels.
        
        Returns:
            List of zoom levels to generate (sorted)
        """
        return sorted(self.selected_zooms)
