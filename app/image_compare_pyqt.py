#!/usr/bin/env python3
"""
Image Comparison Application - PyQt6 Version

A modern GUI application for comparing images side by side or with an overlay slider.
Features:
- Directory selection via file dialog
- Dual list selection for images
- Side-by-side and overlay comparison modes
- Keyboard navigation
- Automatic image scaling
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

from helpers import (
    get_platform_modifier_key, is_image_file, get_image_files_from_directory,
    validate_filename_security, load_pixmap_safe, calculate_text_width
)
from image_cache import get_image_cache
from performance_monitor import get_performance_monitor, measure_performance

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QStatusBar, QSplitter, QGroupBox, QStackedWidget,
    QDialog, QTextEdit, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QAction, QKeySequence, QPainter, QCursor, QPen, QWheelEvent, QColor
from PyQt6.QtCore import Qt, QTimer, QPointF, QEvent

# Import the extracted zoom/pan widget
from zoom_pan_widget import ZoomPanImageLabel
from constants import *


class ImageCompareApp(QMainWindow):
    """Main application window for image comparison."""

    def __init__(self):
        super().__init__()

        # State variables
        self.image_directory = None
        self.image_files = []
        self.left_selection = 0
        self.right_selection = 0
        self.comparison_mode = "side_by_side"  # "side_by_side" or "overlay"
        self.overlay_position = 0.5
        self.overlay_bounds = None
        self.lists_container = None  # Container for top layout
        self.lists_layout = "top"  # "top" or "sides"

        # State saving for splitter sizes
        self.saved_top_layout_sizes = [150, 700]
        self.saved_sides_layout_sizes = [350, 700, 350]
        self.has_auto_sized_sides = False

        # File list visibility state
        self.lists_visible = True
        self.hidden_top_layout_sizes = None
        self.hidden_sides_layout_sizes = None

        # Zoom and pan state
        self.current_zoom = 1.0
        self.current_pan = QPointF(0, 0)
        self.current_image_size = None  # (width, height) tuple
        self.zoom_pan_enabled = False
        self.overlay_split_position = 0.5

        # Initialize image cache for performance
        self.image_cache = get_image_cache()
        
        # Initialize performance monitor
        self.performance_monitor = get_performance_monitor()
        
        # Overlay display cache
        self._overlay_cache_key = None
        self._overlay_cached_pixmap = None

        self.init_ui()
        self.setup_menu()
        self.setup_shortcuts()

        # Initialize header visibility
        self.update_header_visibility()

        # Auto-open directory selection dialog on startup
        QTimer.singleShot(100, self.auto_select_directory)

    def show_performance_stats(self):
        """Show performance statistics in a dialog"""
        stats = self.performance_monitor.get_stats()
        
        stats_text = "Performance Statistics:\n\n"
        
        for operation, metrics in stats.items():
            if operation == 'system':
                continue
                
            stats_text += f"{operation}:\n"
            stats_text += f"  Count: {metrics['count']}\n"
            stats_text += f"  Average time: {metrics['avg_time_ms']} ms\n"
            stats_text += f"  Min time: {metrics['min_time_ms']} ms\n"
            stats_text += f"  Max time: {metrics['max_time_ms']} ms\n"
            stats_text += f"  Total time: {metrics['total_time_s']} s\n\n"
        
        if 'system' in stats:
            sys_stats = stats['system']
            stats_text += f"System:\n"
            stats_text += f"  Process ID: {sys_stats['process_id']}\n"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Performance Statistics")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(stats_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_cache_stats(self):
        """Show cache statistics in a dialog"""
        cache_stats = self.image_cache.get_cache_stats()
        
        stats_text = "Image Cache Statistics:\n\n"
        stats_text += f"Original images cached: {cache_stats['original_count']}\n"
        stats_text += f"Scaled images cached: {cache_stats['scaled_count']}\n"
        stats_text += f"Maximum cache size: {cache_stats['max_size']}\n"
        stats_text += f"Estimated memory usage: {cache_stats['total_memory_mb']} MB\n"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Cache Statistics")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(stats_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def clear_all_caches(self):
        """Clear all caches and reset performance stats"""
        self.image_cache.clear_cache()
        self.performance_monitor.reset_stats()
        self._overlay_cache_key = None
        self._overlay_cached_pixmap = None
        
        QMessageBox.information(self, "Cache Cleared", "All caches have been cleared and performance stats reset.")

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Image Compare")

        # Set window size - Full HD or screen size
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Target Full HD (1920x1080) or use 90% of screen if smaller
        target_width = min(1920, int(screen_geometry.width() * 0.9))
        target_height = min(1080, int(screen_geometry.height() * 0.9))

        # Center the window
        x = (screen_geometry.width() - target_width) // 2
        y = (screen_geometry.height() - target_height) // 2

        self.setGeometry(x, y, target_width, target_height)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Directory selection - fixed height
        dir_widget = QWidget()
        dir_widget.setFixedHeight(60)  # Fixed height for directory selection
        dir_layout = QHBoxLayout(dir_widget)
        self.select_btn = QPushButton("Select Image Directory")
        self.select_btn.clicked.connect(self.select_directory)
        self.select_btn.setMinimumHeight(40)
        self.select_btn.setMaximumHeight(40)

        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("font-weight: bold; color: #666;")

        # Help button
        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_help)
        self.help_btn.setMinimumHeight(40)
        self.help_btn.setMaximumHeight(40)
        self.help_btn.setMaximumWidth(100)

        dir_layout.addWidget(self.select_btn)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addStretch()
        dir_layout.addWidget(self.help_btn)

        main_layout.addWidget(dir_widget)

        # Create main content area
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        # Connect to splitter moved signal to save state when user manually resizes
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)

        # Create file lists widget
        self.create_file_lists()

        # Image display section - completely rewritten for reliability
        self.image_frame = QGroupBox("")  # Remove "Image Comparison" title
        image_layout = QVBoxLayout(self.image_frame)

        # Create a stacked widget to switch between display modes
        from PyQt6.QtWidgets import QStackedWidget
        self.display_stack = QStackedWidget()

        # Side-by-side display widget
        self.sidebyside_widget = QWidget()
        sidebyside_layout = QHBoxLayout(self.sidebyside_widget)
        sidebyside_layout.setContentsMargins(5, 5, 5, 5)

        # Left image container
        left_container = QWidget()
        left_container.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self.left_image_label = ZoomPanImageLabel()
        self.left_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_image_label.setStyleSheet("background-color: #1a1a1a; border: none;")
        self.left_image_label.setMinimumSize(300, 200)
        self.left_image_label.setScaledContents(False)
        self.left_image_label.set_sync_callback(self.sync_zoom_pan)

        self.left_filename_label = QLabel("No image selected")
        self.left_filename_label.setStyleSheet("color: white; font-weight: bold; background-color: #333; padding: 5px;")
        self.left_filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(self.left_filename_label)
        left_layout.addWidget(self.left_image_label, 1)

        # Right image container
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(5, 5, 5, 5)

        self.right_image_label = ZoomPanImageLabel()
        self.right_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_image_label.setStyleSheet("background-color: #1a1a1a; border: none;")
        self.right_image_label.setMinimumSize(300, 200)
        self.right_image_label.setScaledContents(False)
        self.right_image_label.set_sync_callback(self.sync_zoom_pan)

        self.right_filename_label = QLabel("No image selected")
        self.right_filename_label.setStyleSheet("color: white; font-weight: bold; background-color: #333; padding: 5px;")
        self.right_filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.right_filename_label)
        right_layout.addWidget(self.right_image_label, 1)

        sidebyside_layout.addWidget(left_container)
        sidebyside_layout.addWidget(right_container)

        # Overlay display widget with headers
        self.overlay_widget = QWidget()
        overlay_layout = QVBoxLayout(self.overlay_widget)

        # Create overlay headers (initially hidden)
        self.overlay_header_container = QWidget()
        self.overlay_header_container.setFixedHeight(40)  # Fixed height to prevent layout cascading
        overlay_header_layout = QHBoxLayout(self.overlay_header_container)
        overlay_header_layout.setContentsMargins(5, 5, 5, 5)

        # Left filename header for overlay
        self.overlay_left_header = QLabel("No image selected")
        self.overlay_left_header.setStyleSheet("color: white; font-weight: bold; background-color: #333; padding: 5px;")
        self.overlay_left_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay_left_header.setFixedHeight(30)  # Fixed height to prevent resizing during window resize
        self.overlay_left_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Right filename header for overlay
        self.overlay_right_header = QLabel("No image selected")
        self.overlay_right_header.setStyleSheet("color: white; font-weight: bold; background-color: #333; padding: 5px;")
        self.overlay_right_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay_right_header.setFixedHeight(30)  # Fixed height to prevent resizing during window resize
        self.overlay_right_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        overlay_header_layout.addWidget(self.overlay_left_header)
        overlay_header_layout.addWidget(self.overlay_right_header)

        # Initially hide headers (they show when lists are hidden)
        self.overlay_header_container.setVisible(False)
        overlay_layout.addWidget(self.overlay_header_container)

        self.overlay_label = ZoomPanImageLabel()
        self.overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        self.overlay_label.setMinimumSize(600, 400)
        self.overlay_label.setMouseTracking(True)
        self.overlay_label.set_overlay_mode(True)
        self.overlay_label.set_sync_callback(self.sync_zoom_pan)
        overlay_layout.addWidget(self.overlay_label)

        # Add both widgets to stack
        self.display_stack.addWidget(self.sidebyside_widget)  # Index 0
        self.display_stack.addWidget(self.overlay_widget)     # Index 1

        image_layout.addWidget(self.display_stack)

        # Remove the old image_label setup
        # self.image_label = QLabel()...

        # Add widgets to main splitter based on layout
        self.update_layout()

        main_layout.addWidget(self.main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Click 'Select Image Directory' to start comparing images")

    def create_file_lists(self):
        """Create the file list widgets"""
        # Left file list
        self.left_group = QGroupBox("")  # Remove "Left Image" title
        left_layout = QVBoxLayout(self.left_group)
        self.left_listbox = QListWidget()
        self.left_listbox.itemSelectionChanged.connect(self.on_left_select)
        # Set consistent dark orange selection color
        self.left_listbox.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #cc6600;
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #cc6600;
                color: white;
            }
        """)
        left_layout.addWidget(self.left_listbox)

        # Right file list
        self.right_group = QGroupBox("")  # Remove "Right Image" title
        right_layout = QVBoxLayout(self.right_group)
        self.right_listbox = QListWidget()
        self.right_listbox.itemSelectionChanged.connect(self.on_right_select)
        # Set consistent dark orange selection color
        self.right_listbox.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #cc6600;
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #cc6600;
                color: white;
            }
        """)
        right_layout.addWidget(self.right_listbox)

        # Set size constraints based on layout - will be updated in update_layout()
        self.update_list_constraints()

    def update_list_constraints(self):
        """Update list size constraints based on current layout"""
        if self.lists_layout == "top":
            # When lists are on top, constrain height not width
            self.left_group.setMinimumWidth(0)
            self.left_group.setMaximumWidth(16777215)
            self.left_group.setMinimumHeight(80)
            self.left_group.setMaximumHeight(300)
            self.left_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.right_group.setMinimumWidth(0)
            self.right_group.setMaximumWidth(16777215)
            self.right_group.setMinimumHeight(80)
            self.right_group.setMaximumHeight(300)
            self.right_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.left_listbox.setMinimumHeight(50)
            self.right_listbox.setMinimumHeight(50)
        else:
            # When lists are on sides, constrain width not height
            self.left_group.setMinimumWidth(150)
            self.left_group.setMaximumWidth(500)
            self.left_group.setMinimumHeight(0)
            self.left_group.setMaximumHeight(16777215)
            self.left_group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

            self.right_group.setMinimumWidth(150)
            self.right_group.setMaximumWidth(500)
            self.right_group.setMinimumHeight(0)
            self.right_group.setMaximumHeight(16777215)
            self.right_group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

            self.left_listbox.setMinimumHeight(200)
            self.right_listbox.setMinimumHeight(200)

    def update_layout(self):
        """Update the layout based on current lists_layout setting"""
        # Clear splitter by removing all widgets
        for i in reversed(range(self.main_splitter.count())):
            widget = self.main_splitter.widget(i)
            widget.setParent(None)

        # Clean up old container if it exists
        if hasattr(self, 'lists_container') and self.lists_container:
            self.lists_container.deleteLater()
            self.lists_container = None

        if self.lists_layout == "top":
            # Lists on top, images below
            self.lists_container = QWidget()
            self.lists_container.setMinimumHeight(100)
            self.lists_container.setMaximumHeight(400)
            self.lists_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            lists_layout = QHBoxLayout(self.lists_container)
            lists_layout.setContentsMargins(0, 0, 0, 0)
            lists_layout.addWidget(self.left_group)
            lists_layout.addWidget(self.right_group)

            self.main_splitter.setOrientation(Qt.Orientation.Vertical)
            self.main_splitter.addWidget(self.lists_container)
            self.main_splitter.addWidget(self.image_frame)

            # Set stretch factors: lists don't stretch, images get all extra space
            self.main_splitter.setStretchFactor(0, 0)
            self.main_splitter.setStretchFactor(1, 1)
            # Restore saved top layout sizes immediately to prevent flicker
            if self.saved_top_layout_sizes and len(self.saved_top_layout_sizes) == 2:
                QTimer.singleShot(10, lambda: self.restore_splitter_sizes(self.saved_top_layout_sizes))
        else:
            # Lists on sides, images in center
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.main_splitter.addWidget(self.left_group)
            self.main_splitter.addWidget(self.image_frame)
            self.main_splitter.addWidget(self.right_group)

            # Set stretch factors: file lists maintain fixed width, images get extra space
            self.main_splitter.setStretchFactor(0, 0)
            self.main_splitter.setStretchFactor(1, 1)
            self.main_splitter.setStretchFactor(2, 0)
            # Restore saved sides layout sizes immediately to prevent flicker
            if self.saved_sides_layout_sizes and len(self.saved_sides_layout_sizes) == 3:
                QTimer.singleShot(10, lambda: self.restore_splitter_sizes(self.saved_sides_layout_sizes))

        # Update size constraints based on new layout
        self.update_list_constraints()

        # Handle hidden lists after layout change
        if not self.lists_visible:
            # Apply hidden state to new layout
            QTimer.singleShot(20, self.apply_hidden_state)

    def setup_menu(self):
        """Setup the application menu"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        select_action = QAction("Select Directory...", self)
        select_action.setShortcut(QKeySequence("Ctrl+O"))
        select_action.triggered.connect(self.select_directory)
        file_menu.addAction(select_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        side_by_side_action = QAction("Side by Side", self)
        side_by_side_action.triggered.connect(lambda: self.set_comparison_mode("side_by_side"))
        view_menu.addAction(side_by_side_action)

        overlay_action = QAction("Overlay", self)
        overlay_action.triggered.connect(lambda: self.set_comparison_mode("overlay"))
        view_menu.addAction(overlay_action)

        view_menu.addSeparator()

        toggle_action = QAction("Toggle Mode", self)
        toggle_action.setShortcut(QKeySequence("Tab"))
        toggle_action.triggered.connect(self.toggle_comparison_mode)
        view_menu.addAction(toggle_action)

        view_menu.addSeparator()

        layout_action = QAction("Toggle Lists Layout", self)
        layout_action.setShortcut(QKeySequence("Ctrl+L"))
        layout_action.triggered.connect(self.toggle_lists_layout)
        view_menu.addAction(layout_action)

        visibility_action = QAction("Hide/Show Lists", self)
        visibility_action.setShortcut(QKeySequence("Ctrl+K"))
        visibility_action.triggered.connect(self.toggle_lists_visibility)
        view_menu.addAction(visibility_action)

        # Debug menu (only show in development)
        debug_menu = menubar.addMenu("Debug")
        
        perf_stats_action = QAction("Show Performance Stats", self)
        perf_stats_action.triggered.connect(self.show_performance_stats)
        debug_menu.addAction(perf_stats_action)
        
        cache_stats_action = QAction("Show Cache Stats", self)
        cache_stats_action.triggered.connect(self.show_cache_stats)
        debug_menu.addAction(cache_stats_action)
        
        clear_caches_action = QAction("Clear All Caches", self)
        clear_caches_action.triggered.connect(self.clear_all_caches)
        debug_menu.addAction(clear_caches_action)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        left_action = QAction(self)
        left_action.setShortcut(QKeySequence("Left"))
        left_action.triggered.connect(lambda: self.navigate_left_list(-1))
        self.addAction(left_action)

        right_action = QAction(self)
        right_action.setShortcut(QKeySequence("Right"))
        right_action.triggered.connect(lambda: self.navigate_left_list(1))
        self.addAction(right_action)

        up_action = QAction(self)
        up_action.setShortcut(QKeySequence("Up"))
        up_action.triggered.connect(lambda: self.navigate_right_list(-1))
        self.addAction(up_action)

        down_action = QAction(self)
        down_action.setShortcut(QKeySequence("Down"))
        down_action.triggered.connect(lambda: self.navigate_right_list(1))
        self.addAction(down_action)

        # Zoom shortcuts
        zoom_in_ctrl = QAction(self)
        zoom_in_ctrl.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_ctrl.triggered.connect(self.zoom_in)
        self.addAction(zoom_in_ctrl)

        zoom_in_cmd = QAction(self)
        zoom_in_cmd.setShortcut(QKeySequence("Cmd++"))
        zoom_in_cmd.triggered.connect(self.zoom_in)
        self.addAction(zoom_in_cmd)

        zoom_out_ctrl = QAction(self)
        zoom_out_ctrl.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_ctrl.triggered.connect(self.zoom_out)
        self.addAction(zoom_out_ctrl)

        zoom_out_cmd = QAction(self)
        zoom_out_cmd.setShortcut(QKeySequence("Cmd+-"))
        zoom_out_cmd.triggered.connect(self.zoom_out)
        self.addAction(zoom_out_cmd)

        zoom_reset_ctrl = QAction(self)
        zoom_reset_ctrl.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_ctrl.triggered.connect(self.zoom_reset)
        self.addAction(zoom_reset_ctrl)

        zoom_reset_cmd = QAction(self)
        zoom_reset_cmd.setShortcut(QKeySequence("Cmd+0"))
        zoom_reset_cmd.triggered.connect(self.zoom_reset)
        self.addAction(zoom_reset_cmd)

    def sync_zoom_pan(self, zoom, pan):
        """Synchronize zoom and pan across all image widgets"""
        self.current_zoom = zoom
        self.current_pan = pan

        # Update all image labels except the one that triggered this
        sender = self.sender()
        if self.left_image_label != sender:
            self.left_image_label.sync_zoom_pan(zoom, pan)
        if self.right_image_label != sender:
            self.right_image_label.sync_zoom_pan(zoom, pan)
        if self.overlay_label != sender:
            self.overlay_label.sync_zoom_pan(zoom, pan)

    def zoom_in(self):
        """Zoom in on all images"""
        if self.zoom_pan_enabled:
            if self.comparison_mode == "overlay":
                self.overlay_label.zoom_in()
            else:
                self.left_image_label.zoom_in()

    def zoom_out(self):
        """Zoom out on all images"""
        if self.zoom_pan_enabled:
            if self.comparison_mode == "overlay":
                self.overlay_label.zoom_out()
            else:
                self.left_image_label.zoom_out()

    def zoom_reset(self):
        """Reset zoom on all images"""
        if self.zoom_pan_enabled:
            if self.comparison_mode == "overlay":
                self.overlay_label.zoom_reset()
                # Update stored zoom state
                self.current_zoom = self.overlay_label.zoom_factor
                self.current_pan = self.overlay_label.pan_offset
            else:
                self.left_image_label.zoom_reset()
                self.right_image_label.zoom_reset()
                # Update stored zoom state from one of the widgets
                self.current_zoom = self.left_image_label.zoom_factor
                self.current_pan = self.left_image_label.pan_offset

    def check_image_dimensions(self, left_pixmap, right_pixmap):
        """Check if both images have the same dimensions and enable/disable zoom/pan"""
        if left_pixmap and right_pixmap and not left_pixmap.isNull() and not right_pixmap.isNull():
            left_size = left_pixmap.size()
            right_size = right_pixmap.size()

            if left_size == right_size:
                # Same dimensions - enable zoom/pan
                new_image_size = (left_size.width(), left_size.height())

                # Check if image dimensions changed
                if new_image_size != self.current_image_size:
                    # Reset zoom/pan for new image dimensions
                    self.current_image_size = new_image_size
                    # Don't force zoom to 1.0, let widgets calculate fit-to-widget
                    self.current_zoom = None  # Will be set by first widget after reset
                    self.current_pan = QPointF(0, 0)
                    self.zoom_pan_enabled = True

                    # Reset all widgets - they will auto-fit to widget size
                    self.left_image_label.set_original_pixmap(left_pixmap)
                    self.right_image_label.set_original_pixmap(right_pixmap)
                    self.overlay_label.set_overlay_images(left_pixmap, right_pixmap)

                    # Get the zoom factor from one of the widgets after auto-fit
                    self.current_zoom = self.left_image_label.zoom_factor
                else:
                    # Same dimensions as before - keep zoom/pan
                    self.zoom_pan_enabled = True
                    self.left_image_label.set_original_pixmap(left_pixmap)
                    self.right_image_label.set_original_pixmap(right_pixmap)
                    self.overlay_label.set_overlay_images(left_pixmap, right_pixmap)

                    # Apply current zoom/pan
                    self.left_image_label.sync_zoom_pan(self.current_zoom, self.current_pan)
                    self.right_image_label.sync_zoom_pan(self.current_zoom, self.current_pan)
                    self.overlay_label.sync_zoom_pan(self.current_zoom, self.current_pan)

                return True
            else:
                # Different dimensions - disable zoom/pan
                self.zoom_pan_enabled = False
                self.current_image_size = None
                return False
        else:
            # No images or invalid - disable zoom/pan
            self.zoom_pan_enabled = False
            self.current_image_size = None
            return False

    def select_directory(self) -> None:
        """Open file dialog to select image directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Images",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.load_images_from_directory(directory)

    def auto_select_directory(self):
        """Automatically open directory selection dialog on startup"""
        # Only auto-open if no directory is already selected
        if not self.image_directory:
            self.select_directory()

    def show_help(self):
        """Show help dialog with keyboard shortcuts"""
        # Get platform modifier key
        mod_key = get_platform_modifier_key()

        help_text = f"""
<h2>Image Compare - Keyboard Shortcuts<br /></h2>

<h3 style="margin-top: 15px; padding-bottom: 8px;">Application</h3>
<table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px;">
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+O</b></td><td style="background-color: #2a2a2a;">Open directory selection dialog</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+Q</b></td><td style="background-color: #3a3a3a;">Quit application</td></tr>
</table>

<h3 style="margin-top: 20px; padding-bottom: 8px;">Navigation</h3>
<table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px;">
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>Left/Right arrows</b></td><td style="background-color: #2a2a2a;">Navigate left image list</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>Up/Down arrows</b></td><td style="background-color: #3a3a3a;">Navigate right image list</td></tr>
</table>

<h3 style="margin-top: 20px; padding-bottom: 8px;">View Controls</h3>
<table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px;">
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>Tab</b></td><td style="background-color: #2a2a2a;">Toggle between Side-by-Side and Overlay modes</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+L</b></td><td style="background-color: #3a3a3a;">Toggle list layout (top/sides)</td></tr>
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+K</b></td><td style="background-color: #2a2a2a;">Hide/show file lists</td></tr>
</table>

<h3 style="margin-top: 20px; padding-bottom: 8px;">Zoom & Pan (Same-size Images Only)</h3>
<table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px;">
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>Mouse wheel/Trackpad</b></td><td style="background-color: #2a2a2a;">Zoom in/out at mouse position</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>Left click + drag</b></td><td style="background-color: #3a3a3a;">Pan the zoomed image</td></tr>
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}++</b></td><td style="background-color: #2a2a2a;">Zoom in</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+-</b></td><td style="background-color: #3a3a3a;">Zoom out</td></tr>
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>{mod_key}+0</b></td><td style="background-color: #2a2a2a;">Reset zoom to fit view</td></tr>
</table>

<h3 style="margin-top: 20px; padding-bottom: 8px;">Mouse Controls</h3>
<table width="100%" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top: 8px;">
<tr style="background-color: #2a2a2a;"><td width="25%" style="font-weight: bold;"><b>Overlay mode</b></td><td style="background-color: #2a2a2a;">Left click to move divider to position</td></tr>
<tr style="background-color: #3a3a3a;"><td width="25%" style="font-weight: bold;"><b>Overlay + {mod_key}</b></td><td style="background-color: #3a3a3a;">Hold {mod_key} + left click to pan</td></tr>
</table>

<h3 style="margin-top: 20px; padding-bottom: 8px;">Features</h3>
<ul>
<li><b>Zoom/Pan:</b> Only available when both images have identical dimensions</li>
<li><b>Sync:</b> Zoom level and pan position stay synchronized between all views</li>
<li><b>Zoom limits:</b> From fit-to-view to 800% maximum</li>
<li><b>Overlay:</b> Shows zoom percentage in bottom-left corner</li>
</ul>
        """

        # Create custom dialog for better size control
        dialog = QDialog(self)
        dialog.setWindowTitle("Help - Keyboard Shortcuts")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Create text widget for content
        text_widget = QTextEdit()
        text_widget.setHtml(help_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        # Force dialog to be wider and taller to fit all content
        dialog.resize(700, 650)  # Increased height from 520 to 650 for new content
        dialog.exec()

    @measure_performance("load_directory")
    def load_images_from_directory(self, directory: str) -> None:
        """Load all image files from the selected directory"""
        try:
            self.image_directory = directory
            # Clear image caches for new directory
            self.image_cache.clear_cache()
            self._overlay_cache_key = None
            self._overlay_cached_pixmap = None
            
            # Reset auto-sizing flag for new directory
            self.has_auto_sized_sides = False

            # Get valid image files from directory
            valid_image_files, ignored_count = get_image_files_from_directory(directory)

            if not valid_image_files:
                if ignored_count > 0:
                    QMessageBox.critical(self, "Error", "No valid image files found (all files exceed 200MB size limit)!")
                else:
                    QMessageBox.critical(self, "Error", "No image files found in the selected directory!")
                return

            # Sort alphabetically
            self.image_files = sorted([os.path.basename(f) for f in valid_image_files])

            # Update directory label with warning if files were ignored
            dir_name = Path(directory).name or directory
            if ignored_count > 0:
                # Using warning symbol ⚠ - only the warning part in orange
                self.dir_label.setText(f"Directory: {dir_name} | <span style='color: #ff8800;'>⚠ Ignored {ignored_count} images (exceeds max. image size of 200M)</span>")
                self.dir_label.setStyleSheet("font-weight: bold; color: #666;")  # Normal color for directory part
            else:
                self.dir_label.setText(f"Directory: {dir_name}")
                self.dir_label.setStyleSheet("font-weight: bold; color: #666;")  # Normal color

            # Populate listboxes
            self.populate_listboxes()

            # Select first image in both lists
            if self.image_files:
                self.left_selection = 0
                self.right_selection = min(1, len(self.image_files) - 1)

                self.left_listbox.setCurrentRow(self.left_selection)
                self.right_listbox.setCurrentRow(self.right_selection)

                # Auto-size lists if currently in sides layout
                if self.lists_layout == "sides":
                    QTimer.singleShot(50, self.auto_size_side_lists)

                # Update images after a short delay
                QTimer.singleShot(100, self.update_images)

            self.status_bar.showMessage(f"Loaded {len(self.image_files)} images from {dir_name}" +
                                      (f" ({ignored_count} ignored due to size)" if ignored_count > 0 else ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load images: {e}")

    def populate_listboxes(self):
        """Populate both listboxes with image filenames"""
        try:
            # Clear existing items
            self.left_listbox.clear()
            self.right_listbox.clear()

            # Add all image files to both listboxes
            for filename in self.image_files:
                self.left_listbox.addItem(filename)
                self.right_listbox.addItem(filename)

            # Auto-size list width when on sides to fit content
            if self.lists_layout == "sides" and self.image_files:
                self.auto_size_side_lists()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate file lists: {e}")

    def auto_size_side_lists(self):
        """Auto-size the side lists to fit the longest filename"""
        if not self.image_files:
            return

        # Find the longest filename
        longest_filename = max(self.image_files, key=len)

        # Create a temporary QLabel to measure text width
        temp_label = QLabel(longest_filename)
        temp_label.setFont(self.left_listbox.font())

        # Calculate required width (add some padding for scrollbar and margins)
        text_width = temp_label.fontMetrics().boundingRect(longest_filename).width()
        required_width = text_width + 60  # Add padding for scrollbar, margins, etc.

        # Constrain within reasonable bounds
        min_width = 150  # Allow narrower than the calculated width
        max_width = 600
        optimal_width = max(min_width, min(required_width, max_width))

        # Set minimum width to allow narrower resizing, but initial width to optimal
        self.left_group.setMinimumWidth(min_width)  # Allow narrower than optimal
        self.left_group.setMaximumWidth(500)  # Allow wider resizing
        self.right_group.setMinimumWidth(min_width)  # Allow narrower than optimal
        self.right_group.setMaximumWidth(500)  # Allow wider resizing

        # Update splitter sizes with optimal initial width only if no saved sizes exist
        if not self.saved_sides_layout_sizes:
            total_width = self.width()
            side_width = optimal_width
            center_width = total_width - (2 * side_width)
            if center_width > 400:  # Ensure center has minimum space
                self.main_splitter.setSizes([side_width, center_width, side_width])

    def on_left_select(self):
        """Handle left listbox selection"""
        current_row = self.left_listbox.currentRow()
        if current_row >= 0:
            self.left_selection = current_row
            self.update_images()

    def on_right_select(self):
        """Handle right listbox selection"""
        current_row = self.right_listbox.currentRow()
        if current_row >= 0:
            self.right_selection = current_row
            self.update_images()

    def navigate_left_list(self, direction):
        """Navigate left list with keyboard"""
        if not self.image_files:
            return

        new_selection = self.left_selection + direction
        new_selection = max(0, min(new_selection, len(self.image_files) - 1))

        if new_selection != self.left_selection:
            self.left_selection = new_selection
            self.left_listbox.setCurrentRow(self.left_selection)

    def navigate_right_list(self, direction):
        """Navigate right list with keyboard"""
        if not self.image_files:
            return

        new_selection = self.right_selection + direction
        new_selection = max(0, min(new_selection, len(self.image_files) - 1))

        if new_selection != self.right_selection:
            self.right_selection = new_selection
            self.right_listbox.setCurrentRow(self.right_selection)

    def set_comparison_mode(self, mode):
        """Set the comparison mode"""
        self.comparison_mode = mode
        # Removed title setting to keep clean UI
        self.update_images()

    def toggle_comparison_mode(self):
        """Toggle between side-by-side and overlay modes"""
        if self.comparison_mode == "side_by_side":
            self.set_comparison_mode("overlay")
        else:
            self.set_comparison_mode("side_by_side")

    def restore_splitter_sizes(self, sizes):
        """Restore splitter sizes with validation"""
        if not sizes or len(sizes) != self.main_splitter.count():
            return

        self.main_splitter.setSizes(sizes)

        # Force image resize after splitter restoration
        QTimer.singleShot(50, self.update_images)

    def save_current_splitter_state(self):
        """Save the current splitter state based on current layout"""
        if hasattr(self, 'main_splitter') and self.main_splitter.count() > 0:
            current_sizes = self.main_splitter.sizes()

            # Only save if lists are visible to avoid saving hidden (0-size) states
            if self.lists_visible:
                if self.lists_layout == "top":
                    # Currently in top layout, save the sizes
                    self.saved_top_layout_sizes = current_sizes
                elif self.lists_layout == "sides":
                    # Currently in sides layout, save the sizes
                    self.saved_sides_layout_sizes = current_sizes

    def on_splitter_moved(self, pos, index):
        """Handle manual splitter movement to save state"""
        # Only save state if we have files loaded and the layout has been properly set up
        if hasattr(self, 'image_files') and self.image_files:
            # Use a short delay to allow the splitter to finish moving
            QTimer.singleShot(100, self.save_current_splitter_state)

    def toggle_lists_layout(self):
        """Toggle between top and sides layout for file lists"""
        # Save current state before switching (only if lists are visible)
        if self.lists_visible:
            self.save_current_splitter_state()

        # Toggle layout
        if self.lists_layout == "top":
            self.lists_layout = "sides"
        else:
            self.lists_layout = "top"

        self.update_layout()
        # Auto-size lists only if switching to sides for the first time with this directory and lists are visible
        if self.lists_layout == "sides" and self.image_files and not self.has_auto_sized_sides and self.lists_visible:
            QTimer.singleShot(300, self.auto_size_side_lists)
            self.has_auto_sized_sides = True

    def update_header_visibility(self):
        """Update overlay header visibility based on list visibility"""
        # Show overlay headers ONLY when lists are hidden
        if hasattr(self, 'overlay_header_container'):
            self.overlay_header_container.setVisible(not self.lists_visible)

        # Hide side-by-side headers when lists are hidden (they're redundant when lists are visible)
        if hasattr(self, 'left_filename_label') and hasattr(self, 'right_filename_label'):
            self.left_filename_label.setVisible(not self.lists_visible)
            self.right_filename_label.setVisible(not self.lists_visible)

    def toggle_lists_visibility(self):
        """Hide/show file lists while preserving their sizes"""
        if self.lists_visible:
            # Hide lists - save current sizes first
            self.save_current_splitter_state()

            if self.lists_layout == "top":
                # Store current sizes before hiding
                self.hidden_top_layout_sizes = self.main_splitter.sizes().copy()
                # Set lists container to minimal height
                self.main_splitter.setSizes([0, self.main_splitter.sizes()[1]])
            else:
                # Store current sizes before hiding
                self.hidden_sides_layout_sizes = self.main_splitter.sizes().copy()
                # Set file lists to minimal width
                sizes = self.main_splitter.sizes()
                self.main_splitter.setSizes([0, sizes[1], 0])

            # Hide the actual list widgets
            self.left_group.setVisible(False)
            self.right_group.setVisible(False)
            if hasattr(self, 'lists_container') and self.lists_container:
                self.lists_container.setVisible(False)

            self.lists_visible = False
            self.status_bar.showMessage("File lists hidden (Ctrl+K to show)")

        else:
            # Show lists - restore previous sizes
            self.left_group.setVisible(True)
            self.right_group.setVisible(True)
            if hasattr(self, 'lists_container') and self.lists_container:
                self.lists_container.setVisible(True)

            # Restore appropriate sizes based on current layout
            if self.lists_layout == "top":
                if self.hidden_top_layout_sizes and len(self.hidden_top_layout_sizes) == 2:
                    QTimer.singleShot(10, lambda: self.main_splitter.setSizes(self.hidden_top_layout_sizes))
                else:
                    # Fallback to saved sizes if hidden sizes don't exist
                    QTimer.singleShot(10, lambda: self.restore_splitter_sizes(self.saved_top_layout_sizes))
            else:
                if self.hidden_sides_layout_sizes and len(self.hidden_sides_layout_sizes) == 3:
                    QTimer.singleShot(10, lambda: self.main_splitter.setSizes(self.hidden_sides_layout_sizes))
                else:
                    # Fallback to saved sizes if hidden sizes don't exist
                    QTimer.singleShot(10, lambda: self.restore_splitter_sizes(self.saved_sides_layout_sizes))

            self.lists_visible = True
            self.status_bar.showMessage("File lists shown")

        # Update header visibility based on new lists visibility state
        self.update_header_visibility()

        # Force image update after visibility change
        QTimer.singleShot(50, self.update_images)

    def apply_hidden_state(self):
        """Apply hidden state after layout changes"""
        if not self.lists_visible:
            # Hide the widgets
            self.left_group.setVisible(False)
            self.right_group.setVisible(False)
            if hasattr(self, 'lists_container') and self.lists_container:
                self.lists_container.setVisible(False)

            # Set appropriate sizes for hidden state
            if self.lists_layout == "top":
                # In top layout, make lists container height 0
                current_sizes = self.main_splitter.sizes()
                if len(current_sizes) == 2:
                    self.main_splitter.setSizes([0, current_sizes[1]])
            else:
                # In sides layout, make both side lists width 0
                current_sizes = self.main_splitter.sizes()
                if len(current_sizes) == 3:
                    self.main_splitter.setSizes([0, current_sizes[1], 0])

            # Update status message
            self.status_bar.showMessage("File lists hidden (Ctrl+K to show)")

            # Update header visibility
            self.update_header_visibility()

            # Force image update after hiding
            QTimer.singleShot(30, self.update_images)

    @measure_performance("load_image")
    def load_image_simple(self, filename):
        """Simple, reliable image loading with caching for performance"""
        if not self.image_directory or not filename:
            return None

        try:
            # Security: Validate filename
            if not validate_filename_security(filename):
                return None

            image_path = os.path.join(self.image_directory, filename)
            
            # Load image using cache for better performance
            return self.image_cache.get_original_pixmap(image_path)

        except Exception as e:
            # Handle various image loading errors silently
            # Errors are communicated through the UI status and warnings
            return None

    def scale_pixmap_to_label(self, pixmap, label):
        """Scale pixmap to fit in label while maintaining aspect ratio with caching"""
        if not pixmap or pixmap.isNull():
            return None

        label_size = label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return pixmap

        # Use caching for scaled pixmaps if we have the original path
        # For now, fall back to direct scaling since we don't have the path here
        scaled_pixmap = pixmap.scaled(
            label_size.width() - 10,  # Leave some margin
            label_size.height() - 10,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return scaled_pixmap

    def update_images(self):
        """Update displayed images - completely rewritten for reliability"""
        if not self.image_files or self.left_selection < 0 or self.right_selection < 0:
            return

        if self.comparison_mode == "side_by_side":
            self.display_stack.setCurrentIndex(0)  # Show side-by-side widget
            self.update_sidebyside_images()
        else:
            self.display_stack.setCurrentIndex(1)  # Show overlay widget
            self.update_overlay_images()

    def update_sidebyside_images(self):
        """Update side-by-side display with zoom/pan support"""
        try:
            # Load images
            left_filename = self.image_files[self.left_selection]
            left_pixmap = self.load_image_simple(left_filename)

            right_filename = self.image_files[self.right_selection]
            right_pixmap = self.load_image_simple(right_filename)

            # Check dimensions and enable/disable zoom/pan
            dimensions_match = self.check_image_dimensions(left_pixmap, right_pixmap)

            if not dimensions_match:
                # Different dimensions - fall back to simple scaling
                if left_pixmap:
                    scaled_left = self.scale_pixmap_to_label(left_pixmap, self.left_image_label)
                    self.left_image_label.setPixmap(scaled_left)
                    self.left_filename_label.setText(left_filename)
                else:
                    self.left_image_label.clear()
                    self.left_filename_label.setText("Failed to load image")

                if right_pixmap:
                    scaled_right = self.scale_pixmap_to_label(right_pixmap, self.right_image_label)
                    self.right_image_label.setPixmap(scaled_right)
                    self.right_filename_label.setText(right_filename)
                else:
                    self.right_image_label.clear()
                    self.right_filename_label.setText("Failed to load image")
            else:
                # Same dimensions - zoom/pan already handled in check_image_dimensions
                if left_pixmap:
                    self.left_filename_label.setText(left_filename)
                else:
                    self.left_filename_label.setText("Failed to load image")

                if right_pixmap:
                    self.right_filename_label.setText(right_filename)
                else:
                    self.right_filename_label.setText("Failed to load image")

        except Exception as e:
            # Error in side-by-side display - continue silently
            pass

    def update_overlay_images(self):
        """Update overlay display with zoom/pan support"""
        try:
            # Load images
            left_filename = self.image_files[self.left_selection]
            right_filename = self.image_files[self.right_selection]

            # Update overlay headers
            if hasattr(self, 'overlay_left_header') and hasattr(self, 'overlay_right_header'):
                self.overlay_left_header.setText(left_filename)
                self.overlay_right_header.setText(right_filename)

            left_pixmap = self.load_image_simple(left_filename)
            right_pixmap = self.load_image_simple(right_filename)

            # Check dimensions and enable/disable zoom/pan
            dimensions_match = self.check_image_dimensions(left_pixmap, right_pixmap)

            # Sync overlay position from widget before potentially switching modes
            if hasattr(self.overlay_label, 'get_overlay_split_position'):
                self.overlay_split_position = self.overlay_label.get_overlay_split_position()

            if not dimensions_match:
                # Fall back to old overlay method for different dimensions
                if left_pixmap and right_pixmap:
                    self.overlay_label.set_overlay_mode(False)
                    self.create_overlay_display(left_pixmap, right_pixmap, left_filename, right_filename)
            else:
                # Same dimensions - use zoom/pan overlay mode
                self.overlay_label.set_overlay_mode(True)
                self.overlay_label.set_overlay_split_position(self.overlay_split_position)

        except Exception as e:
            # Error in overlay display - continue silently
            pass

    @measure_performance("create_overlay")
    def create_overlay_display(self, left_pixmap, right_pixmap, left_filename, right_filename):
        """Create overlay display with current mouse position and caching"""
        try:
            # Get overlay label size
            label_size = self.overlay_label.size()
            if label_size.width() <= 0 or label_size.height() <= 0:
                return

            # Create cache key to avoid unnecessary regeneration
            cache_key = (left_filename, right_filename, label_size.width(), label_size.height(), self.overlay_split_position)
            
            # Check if we can reuse cached overlay (only if position hasn't changed much)
            if (self._overlay_cache_key == cache_key and 
                self._overlay_cached_pixmap is not None and
                not self._overlay_cached_pixmap.isNull()):
                self.overlay_label.setPixmap(self._overlay_cached_pixmap)
                return

            # Scale both images to the same size - minimal margins for maximum image size
            target_width = label_size.width() - 10  # Reduced from 20 to 10
            target_height = label_size.height() - 10  # Reduced from 20 to 10 for maximum space usage

            left_scaled = left_pixmap.scaled(target_width, target_height,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            right_scaled = right_pixmap.scaled(target_width, target_height,
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)

            # Use the smaller dimensions to ensure both fit
            final_width = min(left_scaled.width(), right_scaled.width())
            final_height = min(left_scaled.height(), right_scaled.height())

            # Re-scale to exact same size
            left_final = left_scaled.scaled(final_width, final_height)
            right_final = right_scaled.scaled(final_width, final_height)

            # Create combined image
            combined_width = label_size.width()
            combined_height = label_size.height()
            combined_pixmap = QPixmap(combined_width, combined_height)
            combined_pixmap.fill(Qt.GlobalColor.black)

            painter = QPainter(combined_pixmap)

            # Center the images - no filename space needed
            x_offset = (combined_width - final_width) // 2
            y_offset = (combined_height - final_height) // 2  # Center vertically without filename space

            # Draw right image as background
            painter.drawPixmap(x_offset, y_offset, right_final)

            # Get mouse position for split - use relative position for persistence
            mouse_pos = self.overlay_label.mapFromGlobal(QCursor.pos())
            
            # Convert stored relative position to pixel position for this image
            split_x = int(final_width * self.overlay_split_position)

            # Update split based on mouse if over image
            if (x_offset <= mouse_pos.x() <= x_offset + final_width and
                y_offset <= mouse_pos.y() <= y_offset + final_height):
                split_x = mouse_pos.x() - x_offset
                # Store as relative position (0.0 to 1.0) for persistence across image changes
                self.overlay_split_position = split_x / final_width if final_width > 0 else 0.5

            # Draw left image with clipping
            if split_x > 0:
                painter.setClipRect(x_offset, y_offset, split_x, final_height)
                painter.drawPixmap(x_offset, y_offset, left_final)
                painter.setClipping(False)

            painter.end()

            # Cache the result
            self._overlay_cache_key = cache_key
            self._overlay_cached_pixmap = combined_pixmap

            self.overlay_label.setPixmap(combined_pixmap)

        except Exception as e:
            # Error creating overlay - continue silently
            pass

    def overlay_mouse_move(self, event):
        """Handle mouse movement in overlay mode"""
        if self.comparison_mode == "overlay" and self.image_files:
            # Simply update the overlay display
            self.update_overlay_images()

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)

        # Update images when window is resized
        QTimer.singleShot(100, self.update_images)

    def toggle_comparison_mode(self):
        """Toggle between side-by-side and overlay modes"""
        if self.comparison_mode == "side_by_side":
            self.set_comparison_mode("overlay")
        else:
            self.set_comparison_mode("side_by_side")


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("Image Compare")
    app.setApplicationDisplayName("Image Compare")

    window = ImageCompareApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
