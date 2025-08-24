#!/usr/bin/env python3
"""
Custom QLabel widget with zoom and pan capabilities for image display.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QPointF
from constants import MIN_ZOOM_RATIO, MAX_ZOOM_RATIO


class ZoomPanImageLabel(QLabel):
    """Custom QLabel with zoom and pan capabilities"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Zoom and pan state
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.original_pixmap = None
        self.is_dragging = False
        self.last_mouse_pos = QPointF()

        # Cached scaled pixmaps for performance
        self.cached_left_scaled = None
        self.cached_right_scaled = None
        self.cached_regular_scaled = None
        self.cached_zoom_factor = None

        # Zoom limits
        self.min_zoom = 0.1  # Will be calculated based on fit-to-widget
        self.min_zoom_ratio = MIN_ZOOM_RATIO  # From constants
        self.max_zoom_ratio = MAX_ZOOM_RATIO  # From constants

        # Overlay mode settings
        self.overlay_mode = False
        self.overlay_split_position = 0.5  # 0.0 = all left, 1.0 = all right
        self.right_image_pixmap = None
        self.overlay_drag_mode = False

        # Sync callback for coordinating with other widgets
        self.sync_callback = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)

    def set_sync_callback(self, callback):
        """Set callback function for syncing zoom/pan with other widgets"""
        self.sync_callback = callback

    def set_overlay_mode(self, is_overlay):
        """Enable or disable overlay mode"""
        self.overlay_mode = is_overlay
        # Invalidate cache when switching modes
        self.cached_left_scaled = None
        self.cached_right_scaled = None
        self.cached_regular_scaled = None

    def set_overlay_images(self, left_pixmap, right_pixmap):
        """Set both images for overlay mode"""
        self.original_pixmap = left_pixmap
        self.right_image_pixmap = right_pixmap
        # Invalidate cache when images change
        self.cached_left_scaled = None
        self.cached_right_scaled = None
        self.cached_regular_scaled = None
        self.cached_zoom_factor = None
        if self.overlay_mode:
            self.update_display()

    def set_overlay_split_position(self, position):
        """Set the overlay split position (0.0 = all left, 1.0 = all right)"""
        self.overlay_split_position = max(0.0, min(1.0, position))
        if self.overlay_mode:
            self.update_display()

    def get_overlay_split_position(self):
        """Get the current overlay split position (0.0 = all left, 1.0 = all right)"""
        return self.overlay_split_position

    def mouse_to_split_position(self, mouse_x):
        """Convert mouse x coordinate to split position (0.0 to 1.0)"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return 0.5

        widget_size = self.size()
        display_zoom = self.get_display_zoom()
        scaled_size = self.original_pixmap.size() * display_zoom

        # Calculate where the image is drawn
        center_x = widget_size.width() / 2
        draw_x = center_x - scaled_size.width() / 2 + self.pan_offset.x()

        # Convert mouse x to position within the image
        if scaled_size.width() <= 0:
            return 0.5

        image_relative_x = mouse_x - draw_x
        split_position = max(0.0, min(1.0, image_relative_x / scaled_size.width()))

        return split_position

    def set_original_pixmap(self, pixmap):
        """Set the original pixmap and reset zoom/pan"""
        self.original_pixmap = pixmap
        # Invalidate cache when image changes
        self.cached_left_scaled = None
        self.cached_right_scaled = None
        self.cached_regular_scaled = None
        self.cached_zoom_factor = None

        if pixmap and not pixmap.isNull():
            # Ensure we have a valid widget size before calculating zoom
            self.calculate_min_zoom()
            # If widget size is not ready yet, min_zoom might be wrong
            # Force a reset on the next update
            if self.size().width() <= 0 or self.size().height() <= 0:
                # Widget not properly sized yet, use original size for now
                self.zoom_factor = 1.0
            else:
                self.zoom_factor = self.min_zoom  # Fit to widget
            self.pan_offset = QPointF(0, 0)
            self.update_display()
        else:
            self.clear()

    def calculate_min_zoom(self):
        """Calculate minimum zoom to fit image in widget"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        widget_size = self.size()
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            return

        pixmap_size = self.original_pixmap.size()

        # Calculate scale factors for both dimensions to fit in widget
        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()

        # Use the smaller scale to ensure the image fits entirely
        self.min_zoom = min(scale_x, scale_y)

        # The minimum zoom_factor should be the scale needed to fit image in widget
        # Since zoom_factor now directly represents zoom relative to original image,
        # and we want minimum zoom to fit the image exactly in the widget,
        # min_zoom_ratio should be the same as min_zoom
        self.min_zoom_ratio = self.min_zoom

    def reset_view(self):
        """Reset zoom and pan to default (fit to widget)"""
        self.calculate_min_zoom()
        self.zoom_factor = self.min_zoom  # Fit to widget
        self.pan_offset = QPointF(0, 0)
        self.update_display()

    def get_display_zoom(self):
        """Get the actual display zoom factor (zoom relative to original image size)"""
        return self.zoom_factor

    def sync_zoom_pan(self, zoom, pan):
        """Sync zoom and pan from another widget"""
        self.zoom_factor = zoom
        self.pan_offset = pan
        self.update_display()

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        # Get wheel delta
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9

        # Calculate zoom center (mouse position)
        mouse_pos = event.position()
        self.zoom_at_point(zoom_factor, mouse_pos)

    def mousePressEvent(self, event):
        """Handle mouse press for panning or overlay dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.overlay_mode:
                # In overlay mode, check for Cmd/Ctrl modifier for panning
                modifiers = event.modifiers()
                if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                    # Pan mode
                    self.is_dragging = True
                    self.last_mouse_pos = event.position()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                else:
                    # Overlay divider drag mode
                    self.overlay_drag_mode = True
                    # Jump divider to click position
                    split_pos = self.mouse_to_split_position(event.position().x())
                    self.set_overlay_split_position(split_pos)
            else:
                # Regular pan mode for side-by-side
                self.is_dragging = True
                self.last_mouse_pos = event.position()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Handle mouse move for panning or overlay dragging"""
        if self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            # Pan the image
            if not self.original_pixmap or self.original_pixmap.isNull():
                return

            current_pos = event.position()
            delta = current_pos - self.last_mouse_pos

            self.pan_offset += delta
            self.clamp_pan()
            self.update_display()

            self.last_mouse_pos = current_pos

            # Notify other widgets
            if self.sync_callback:
                self.sync_callback(self.zoom_factor, self.pan_offset)

        elif self.overlay_drag_mode and (event.buttons() & Qt.MouseButton.LeftButton):
            # Update overlay divider position
            split_pos = self.mouse_to_split_position(event.position().x())
            self.set_overlay_split_position(split_pos)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.overlay_drag_mode = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def zoom_at_point(self, zoom_delta, point):
        """Zoom at a specific point (usually mouse position)"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        old_zoom = self.zoom_factor
        new_zoom = old_zoom * zoom_delta

        # Clamp zoom to limits (relative to original image size)
        new_zoom = max(self.min_zoom_ratio, min(self.max_zoom_ratio, new_zoom))

        if new_zoom == old_zoom:
            return  # No change

        # Calculate the point in image coordinates
        widget_center = QPointF(self.width() / 2, self.height() / 2)
        zoom_point = point - widget_center - self.pan_offset

        # Adjust pan to keep the zoom point in the same screen position
        zoom_ratio = new_zoom / old_zoom
        self.pan_offset = self.pan_offset * zoom_ratio + zoom_point * (1 - zoom_ratio)
        self.zoom_factor = new_zoom

        self.clamp_pan()
        self.update_display()

        # Notify other widgets
        if self.sync_callback:
            self.sync_callback(self.zoom_factor, self.pan_offset)

    def clamp_pan(self):
        """Clamp pan to prevent image from going out of bounds"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return

        widget_size = self.size()
        display_zoom = self.get_display_zoom()
        scaled_size = self.original_pixmap.size() * display_zoom

        # Calculate maximum pan offsets
        max_x = max(0, (scaled_size.width() - widget_size.width()) / 2)
        max_y = max(0, (scaled_size.height() - widget_size.height()) / 2)

        # Clamp pan offset
        self.pan_offset.setX(max(-max_x, min(max_x, self.pan_offset.x())))
        self.pan_offset.setY(max(-max_y, min(max_y, self.pan_offset.y())))

    def update_display(self):
        """Update the displayed image with current zoom and pan"""
        if not self.original_pixmap or self.original_pixmap.isNull():
            self.clear()
            return

        # Create a pixmap for the widget
        widget_size = self.size()
        display_pixmap = QPixmap(widget_size)
        display_pixmap.fill(Qt.GlobalColor.black)

        painter = QPainter(display_pixmap)

        if self.overlay_mode and self.right_image_pixmap and not self.right_image_pixmap.isNull():
            # Overlay mode - draw both images with split

            # Check if we need to regenerate scaled pixmaps
            display_zoom = self.get_display_zoom()
            if (self.cached_zoom_factor != display_zoom or
                self.cached_left_scaled is None or
                self.cached_right_scaled is None):

                # Generate scaled pixmaps
                scaled_size = self.original_pixmap.size() * display_zoom
                self.cached_left_scaled = self.original_pixmap.scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cached_right_scaled = self.right_image_pixmap.scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cached_zoom_factor = display_zoom

            # Use cached scaled pixmaps
            left_scaled = self.cached_left_scaled
            right_scaled = self.cached_right_scaled

            # Calculate position to draw the scaled pixmaps
            center_x = widget_size.width() / 2
            center_y = widget_size.height() / 2

            draw_x = center_x - left_scaled.width() / 2 + self.pan_offset.x()
            draw_y = center_y - left_scaled.height() / 2 + self.pan_offset.y()

            # Draw right image as background
            painter.drawPixmap(int(draw_x), int(draw_y), right_scaled)

            # Draw left image with clipping based on split position
            split_x = int(left_scaled.width() * self.overlay_split_position)
            if split_x > 0:
                painter.setClipRect(int(draw_x), int(draw_y), split_x, left_scaled.height())
                painter.drawPixmap(int(draw_x), int(draw_y), left_scaled)
                painter.setClipping(False)

                # Split line is invisible (0px width)
        else:
            # Regular mode - single image

            # Check if we need to regenerate scaled pixmap
            display_zoom = self.get_display_zoom()
            if (self.cached_zoom_factor != display_zoom or
                self.cached_regular_scaled is None):

                # Generate scaled pixmap
                scaled_size = self.original_pixmap.size() * display_zoom
                self.cached_regular_scaled = self.original_pixmap.scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cached_zoom_factor = display_zoom

            # Use cached scaled pixmap
            scaled_pixmap = self.cached_regular_scaled

            # Calculate position to draw the scaled pixmap
            center_x = widget_size.width() / 2
            center_y = widget_size.height() / 2

            draw_x = center_x - scaled_pixmap.width() / 2 + self.pan_offset.x()
            draw_y = center_y - scaled_pixmap.height() / 2 + self.pan_offset.y()

            # Draw the scaled pixmap
            painter.drawPixmap(int(draw_x), int(draw_y), scaled_pixmap)

        # Draw zoom level overlay (relative to original image size)
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Current actual display size compared to original image size
            display_zoom = self.get_display_zoom()

            # Calculate percentage relative to original image size (100% = original pixel size)
            # zoom_factor now directly represents zoom relative to original image
            zoom_percentage = int(self.zoom_factor * 100)
        else:
            zoom_percentage = 100

        zoom_text = f"{zoom_percentage}%"

        # Semi-transparent background for zoom overlay
        painter.setPen(QColor(255, 255, 255, 200))  # Semi-transparent white text
        painter.fillRect(10, widget_size.height() - 30, 80, 20,
                        QColor(0, 0, 0, 128))  # Semi-transparent black background
        painter.drawText(15, widget_size.height() - 15, zoom_text)

        painter.end()

        self.setPixmap(display_pixmap)

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        if self.original_pixmap and not self.original_pixmap.isNull():
            old_min_zoom_ratio = self.min_zoom_ratio
            self.calculate_min_zoom()

            # If zoom is currently at 1.0 (100%) and we now have proper widget size,
            # and this is likely the first proper sizing, fit to widget
            if (self.zoom_factor == 1.0 and
                self.size().width() > 0 and self.size().height() > 0 and
                old_min_zoom_ratio != self.min_zoom_ratio):
                # This is likely the initial sizing after image load, fit to widget
                self.zoom_factor = self.min_zoom_ratio
                if self.sync_callback:
                    self.sync_callback(self.zoom_factor, self.pan_offset)
            elif self.zoom_factor < self.min_zoom_ratio:
                # Normal case: if zoomed too far out, clamp to minimum
                self.zoom_factor = self.min_zoom_ratio
                if self.sync_callback:
                    self.sync_callback(self.zoom_factor, self.pan_offset)

            self.clamp_pan()
            self.update_display()

    # Keyboard shortcut methods
    def zoom_in(self):
        """Zoom in by 10%"""
        center = QPointF(self.width() / 2, self.height() / 2)
        self.zoom_at_point(1.1, center)

    def zoom_out(self):
        """Zoom out by 10%"""
        center = QPointF(self.width() / 2, self.height() / 2)
        self.zoom_at_point(0.9, center)

    def zoom_reset(self):
        """Reset zoom to fit image"""
        self.reset_view()
