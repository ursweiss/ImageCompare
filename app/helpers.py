#!/usr/bin/env python3
"""
Helper functions and utilities for the Image Compare application.
"""

import os
import platform
from typing import List, Tuple
from PyQt6.QtGui import QPixmap, QFontMetrics
from PyQt6.QtWidgets import QWidget
from constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE


def get_platform_modifier_key() -> str:
    """Get the appropriate modifier key for the current platform."""
    return "Cmd" if platform.system() == "Darwin" else "Ctrl"


def is_image_file(file_path: str) -> bool:
    """Check if file is a supported image format."""
    return any(file_path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)


def get_image_files_from_directory(directory: str) -> Tuple[List[str], int]:
    """
    Get all valid image files from a directory.
    
    Args:
        directory: Path to the directory to scan
        
    Returns:
        Tuple of (valid_files, ignored_count)
    """
    if not os.path.isdir(directory):
        return [], 0
    
    valid_files = []
    ignored_count = 0
    
    try:
        # Get all files in directory
        all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        for filename in all_files:
            if is_image_file(filename):
                file_path = os.path.join(directory, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size <= MAX_FILE_SIZE:
                        valid_files.append(file_path)
                    else:
                        ignored_count += 1
                except OSError:
                    ignored_count += 1
                    continue
    
    except OSError:
        return [], 0
    
    return sorted(valid_files), ignored_count


def validate_filename_security(filename: str) -> bool:
    """
    Validate filename for security (prevent path traversal).
    
    Args:
        filename: The filename to validate
        
    Returns:
        True if filename is safe, False otherwise
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    dangerous_chars = ["..", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    return not any(char in filename for char in dangerous_chars)


def load_pixmap_safe(image_path: str) -> QPixmap:
    """
    Safely load a pixmap with error handling.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        QPixmap if successful, None if failed
    """
    if not os.path.exists(image_path):
        return None
    
    try:
        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > MAX_FILE_SIZE:
            return None
        
        # Load the pixmap
        pixmap = QPixmap(image_path)
        return pixmap if not pixmap.isNull() else None
        
    except Exception:
        return None


def calculate_text_width(text: str, widget: QWidget) -> int:
    """
    Calculate the pixel width of text in a widget.
    
    Args:
        text: The text to measure
        widget: Widget to get font metrics from
        
    Returns:
        Width in pixels
    """
    font_metrics = QFontMetrics(widget.font())
    return font_metrics.horizontalAdvance(text)


def scale_pixmap_to_fit(pixmap: QPixmap, max_width: int, max_height: int) -> QPixmap:
    """
    Scale a pixmap to fit within the given dimensions while maintaining aspect ratio.
    
    Args:
        pixmap: The pixmap to scale
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Scaled pixmap
    """
    if pixmap.isNull():
        return pixmap
    
    from PyQt6.QtCore import Qt
    return pixmap.scaled(
        max_width, max_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))
