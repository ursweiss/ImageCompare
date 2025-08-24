#!/usr/bin/env python3
"""
Image caching system for the Image Compare application.
Provides efficient pixmap caching to avoid repeated image loading and scaling operations.
"""

from typing import Dict, Optional, Tuple
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize
import os
from constants import MAX_FILE_SIZE


class ImageCache:
    """
    LRU cache for loaded and scaled pixmaps to improve performance.
    """
    
    def __init__(self, max_cache_size: int = 50):
        """
        Initialize the image cache.
        
        Args:
            max_cache_size: Maximum number of images to cache
        """
        self.max_cache_size = max_cache_size
        self._original_cache: Dict[str, QPixmap] = {}
        self._scaled_cache: Dict[Tuple[str, int, int], QPixmap] = {}
        self._access_order: Dict[str, int] = {}
        self._scaled_access_order: Dict[Tuple[str, int, int], int] = {}
        self._access_counter = 0
    
    def get_original_pixmap(self, image_path: str) -> Optional[QPixmap]:
        """
        Get original pixmap from cache or load it.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            QPixmap if successful, None if failed
        """
        if image_path in self._original_cache:
            # Update access order
            self._access_counter += 1
            self._access_order[image_path] = self._access_counter
            return self._original_cache[image_path]
        
        # Load the image
        pixmap = self._load_pixmap_safe(image_path)
        if pixmap is not None:
            self._add_original_to_cache(image_path, pixmap)
        
        return pixmap
    
    def get_scaled_pixmap(self, image_path: str, width: int, height: int) -> Optional[QPixmap]:
        """
        Get scaled pixmap from cache or create it.
        
        Args:
            image_path: Path to the image file
            width: Target width
            height: Target height
            
        Returns:
            Scaled QPixmap if successful, None if failed
        """
        cache_key = (image_path, width, height)
        
        if cache_key in self._scaled_cache:
            # Update access order
            self._access_counter += 1
            self._scaled_access_order[cache_key] = self._access_counter
            return self._scaled_cache[cache_key]
        
        # Get original pixmap first
        original_pixmap = self.get_original_pixmap(image_path)
        if original_pixmap is None:
            return None
        
        # Scale the pixmap
        from PyQt6.QtCore import Qt
        scaled_pixmap = original_pixmap.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Add to scaled cache
        self._add_scaled_to_cache(cache_key, scaled_pixmap)
        
        return scaled_pixmap
    
    def invalidate_image(self, image_path: str) -> None:
        """
        Remove an image from all caches (when file changes).
        
        Args:
            image_path: Path to the image file
        """
        # Remove from original cache
        if image_path in self._original_cache:
            del self._original_cache[image_path]
            del self._access_order[image_path]
        
        # Remove from scaled cache
        keys_to_remove = [key for key in self._scaled_cache.keys() if key[0] == image_path]
        for key in keys_to_remove:
            del self._scaled_cache[key]
            del self._scaled_access_order[key]
    
    def clear_cache(self) -> None:
        """Clear all cached images."""
        self._original_cache.clear()
        self._scaled_cache.clear()
        self._access_order.clear()
        self._scaled_access_order.clear()
        self._access_counter = 0
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'original_count': len(self._original_cache),
            'scaled_count': len(self._scaled_cache),
            'max_size': self.max_cache_size,
            'total_memory_mb': self._estimate_memory_usage()
        }
    
    def _load_pixmap_safe(self, image_path: str) -> Optional[QPixmap]:
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
    
    def _add_original_to_cache(self, image_path: str, pixmap: QPixmap) -> None:
        """Add original pixmap to cache with LRU eviction."""
        # Check if we need to evict
        if len(self._original_cache) >= self.max_cache_size:
            self._evict_oldest_original()
        
        # Add to cache
        self._access_counter += 1
        self._original_cache[image_path] = pixmap
        self._access_order[image_path] = self._access_counter
    
    def _add_scaled_to_cache(self, cache_key: Tuple[str, int, int], pixmap: QPixmap) -> None:
        """Add scaled pixmap to cache with LRU eviction."""
        # Check if we need to evict
        if len(self._scaled_cache) >= self.max_cache_size * 2:  # Allow more scaled images
            self._evict_oldest_scaled()
        
        # Add to cache
        self._access_counter += 1
        self._scaled_cache[cache_key] = pixmap
        self._scaled_access_order[cache_key] = self._access_counter
    
    def _evict_oldest_original(self) -> None:
        """Evict the least recently used original pixmap."""
        if not self._access_order:
            return
        
        oldest_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        del self._original_cache[oldest_key]
        del self._access_order[oldest_key]
    
    def _evict_oldest_scaled(self) -> None:
        """Evict the least recently used scaled pixmap."""
        if not self._scaled_access_order:
            return
        
        oldest_key = min(self._scaled_access_order.keys(), key=lambda k: self._scaled_access_order[k])
        del self._scaled_cache[oldest_key]
        del self._scaled_access_order[oldest_key]
    
    def _estimate_memory_usage(self) -> int:
        """
        Estimate memory usage in MB.
        
        Returns:
            Estimated memory usage in megabytes
        """
        total_bytes = 0
        
        # Estimate original pixmaps
        for pixmap in self._original_cache.values():
            if not pixmap.isNull():
                # Rough estimate: width * height * 4 bytes per pixel (RGBA)
                total_bytes += pixmap.width() * pixmap.height() * 4
        
        # Estimate scaled pixmaps
        for pixmap in self._scaled_cache.values():
            if not pixmap.isNull():
                total_bytes += pixmap.width() * pixmap.height() * 4
        
        return total_bytes // (1024 * 1024)  # Convert to MB


# Global cache instance
_global_cache = ImageCache()


def get_image_cache() -> ImageCache:
    """Get the global image cache instance."""
    return _global_cache
