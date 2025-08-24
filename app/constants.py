#!/usr/bin/env python3
"""
Application constants and configuration values.
"""

# Application metadata
APP_NAME = "Image Compare"
APP_VERSION = "2.0.0"

# File handling constants
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB in bytes
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

# UI layout constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_LIST_WIDTH = 200
MAX_LIST_WIDTH = 600
MIN_LIST_HEIGHT = 100

# Splitter timing constants (in milliseconds)
SPLITTER_TIMER_DELAY = 100
AUTO_SIZE_DELAY = 50
HIDDEN_STATE_DELAY = 100
IMAGE_UPDATE_DELAY = 30

# Colors and styling
SELECTION_COLOR = "#0066CC"
BACKGROUND_COLOR = "#2B2B2B"
BORDER_COLOR = "#555555"
TEXT_COLOR = "#FFFFFF"
WARNING_COLOR = "#FF6B35"

# Zoom and pan constants
MIN_ZOOM_RATIO = 0.01  # 1% minimum zoom
MAX_ZOOM_RATIO = 50.0  # 50x maximum zoom  
ZOOM_STEP = 1.1  # 10% zoom step

# Help dialog size
HELP_DIALOG_WIDTH = 600
HELP_DIALOG_HEIGHT = 500
