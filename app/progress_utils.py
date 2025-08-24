#!/usr/bin/env python3
"""
Progress tracking utilities for long-running operations.
"""

from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Callable, List, Any
import time


class ProgressTracker:
    """Simple progress tracking for operations."""
    
    def __init__(self, title: str = "Processing...", parent=None):
        self.title = title
        self.parent = parent
        self.progress_dialog = None
        self.cancelled = False
    
    def start(self, max_value: int, label: str = ""):
        """Start showing progress dialog."""
        self.progress_dialog = QProgressDialog(label, "Cancel", 0, max_value, self.parent)
        self.progress_dialog.setWindowTitle(self.title)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(500)  # Show after 500ms
        self.progress_dialog.canceled.connect(self._on_cancel)
        self.cancelled = False
    
    def update(self, value: int, label: str = None):
        """Update progress value and optionally label."""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            if label:
                self.progress_dialog.setLabelText(label)
            QApplication.processEvents()  # Keep UI responsive
    
    def finish(self):
        """Close progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self.cancelled
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True


class WorkerThread(QThread):
    """Generic worker thread for background operations."""
    
    # Signals
    progress = pyqtSignal(int, str)  # value, label
    finished_with_result = pyqtSignal(object)  # result
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, worker_func: Callable, *args, **kwargs):
        super().__init__()
        self.worker_func = worker_func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def cancel(self):
        """Cancel the operation."""
        self._cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled
    
    def run(self):
        """Run the worker function."""
        try:
            # Add progress callback to kwargs
            self.kwargs['progress_callback'] = self._emit_progress
            self.kwargs['is_cancelled_callback'] = self.is_cancelled
            
            result = self.worker_func(*self.args, **self.kwargs)
            
            if not self._cancelled:
                self.finished_with_result.emit(result)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _emit_progress(self, value: int, label: str = ""):
        """Emit progress signal."""
        self.progress.emit(value, label)
