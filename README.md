# Image Compare Application

> **Disclaimer**: This application was primarily written by AI (GitHub Copilot and Claude) with human guidance and revi## Project Structure

```
ImageCompare/
├── app/                         # Application source code
│   ├── image_compare_pyqt.py    # Main PyQt6 application
│   ├── zoom_pan_widget.py       # Custom zoom/pan widget
│   ├── image_cache.py          # LRU caching system
│   ├── performance_monitor.py  # Performance tracking
│   ├── progress_utils.py       # Progress dialog utilities
│   ├── helpers.py              # Utility functions
│   ├── constants.py            # Application constants
│   └── create_test_images.py   # Test image generator
├── setup/                       # Setup scripts
│   ├── setup.sh                # macOS/Linux setup script
│   ├── setup.bat               # Windows setup script
│   └── requirements.txt        # Python dependencies
├── run.sh                      # macOS/Linux run script
├── run.bat                     # Windows run script
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── test_images/                # Generated test images (git-ignored)
└── venv/                       # Virtual environment (git-ignored)
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Main Application** (`image_compare_pyqt.py`): Core UI and application logic
- **Custom Widgets** (`zoom_pan_widget.py`): Specialized image display with zoom/pan
- **Caching System** (`image_cache.py`): LRU cache for performance optimization
- **Performance Monitoring** (`performance_monitor.py`): Real-time performance tracking
- **Helper Functions** (`helpers.py`): Utility functions for common operations
- **Constants** (`constants.py`): Centralized configuration management has been tested and reviewed for functionality and security, users should exercise appropriate caution when using AI-generated code in production environments.

A modern, high-performance Python GUI application for comparing images within a directory. Built with PyQt6 and optimized for speed and reliability.

## Features

### Core Functionality
- **Large File Handling**: Automatically filters out images larger than 200MB to prevent memory issues
- **Dual Image Lists**: Two synchronized lists showing all images in alphabetical order with adjustable widths
- **Two Comparison Modes**:
  - **Side by Side**: Shows selected images next to each other with synchronized zoom/pan
  - **Overlay**: Shows images overlapping with an adjustable mouse-controlled divider
- **Layout Options**: 
  - Toggle between top and left/right list arrangements
  - Hide/show file lists for distraction-free viewing
- **Automatic Scaling**: Images are automatically scaled to fit the display area while maintaining aspect ratio

### Performance Optimizations
- **Advanced Image Caching**: LRU cache system for both original and scaled images
- **Smart Overlay Caching**: Reduced redundant composite image generation
- **Memory Management**: Intelligent cache eviction and cleanup
- **Performance Monitoring**: Built-in tools to track application performance
- **Responsive UI**: Background operations keep interface smooth

### Advanced Features
- **Zoom and Pan** (for images with same dimensions):
  - Synchronized zoom/pan across all view modes
  - State persistence when switching between images
  - Mouse wheel and trackpad support
- **Security Features**: Path validation and safe file handling
- **Debug Tools**: Performance statistics and cache monitoring (Debug menu)
- **Cross-Platform**: Native keyboard shortcuts for macOS, Windows, and Linux
- **Keyboard Navigation**:
  - `Left/Right arrows`: Navigate the left image list
  - `Up/Down arrows`: Navigate the right image list
  - `Tab`: Toggle between comparison modes
  - `Cmd+L` (Mac) / `Ctrl+L` (Windows/Linux): Toggle list layout (top/sides)
  - `Cmd+K` (Mac) / `Ctrl+K` (Windows/Linux): Hide/show file lists
  - `Cmd+O` (Mac) / `Ctrl+O` (Windows/Linux): Open directory selection dialog
  - `Cmd+Q` (Mac) / `Ctrl+Q` (Windows/Linux): Quit application
- **Zoom and Pan (for images with same dimensions only)**:
  - `Mouse wheel` / `Trackpad pinch`: Zoom in/out
  - `Click and drag`: Pan around zoomed images
  - `Cmd+0` (Mac) / `Ctrl+0` (Windows/Linux): Reset zoom to fit view
  - `Cmd++` (Mac) / `Ctrl++` (Windows/Linux): Zoom in
  - `Cmd+-` (Mac) / `Ctrl+-` (Windows/Linux): Zoom out
- **Mouse Interaction**: 
  - In overlay mode, click and drag to move the divider (hold Cmd/Ctrl while dragging to pan instead)
  - Zoom/pan is synchronized between both images and preserved when switching views
- **Automatic Scaling**: Images are automatically scaled to fit the display area while maintaining aspect ratio

## Installation

### Quick Setup (Recommended)

Use the provided setup script for your platform:

**macOS/Linux:**
```bash
./setup/setup.sh
```

**Windows:**
```batch
setup\setup.bat
```

### Manual Setup

1. Make sure you have Python 3.x installed
2. Create and activate a virtual environment:
   ```bash
   # macOS/Linux
   /usr/bin/python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate.bat
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

**macOS/Linux:**
```bash
./run.sh
```

**Windows:**
```batch
run.bat
```

**Manual:**
```bash
# macOS/Linux
source venv/bin/activate
python app/image_compare_pyqt.py

# Windows
venv\Scripts\activate.bat
python app\image_compare_pyqt.py
```

### Creating Test Images

To create sample images for testing the application:
```bash
# macOS/Linux
source venv/bin/activate
python app/create_test_images.py

# Windows
venv\Scripts\activate.bat
python app\create_test_images.py
```

This will create a `test_images` directory with 8 different sample images including gradients, patterns, and text images.

### Getting Started

1. When the application starts, it will automatically open a directory selection dialog
2. Choose a directory containing image files (supports JPG, PNG, BMP, TIFF, GIF)
3. If no images are found, an error message will be displayed
4. Use the two lists to select images for comparison (click with mouse or use arrow keys)
5. Images will be displayed in the center area
6. Use keyboard shortcuts or the menu to switch between comparison modes

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- GIF (.gif)

## Requirements

- Python 3.x 
- PyQt6 >= 6.5.0
- Pillow >= 10.0.0

## Project Structure

```
ImageCompare/
├── app/                         # Application files
│   ├── image_compare_pyqt.py    # Main PyQt6 application
│   └── create_test_images.py    # Test image generator
├── setup/                       # Setup scripts
│   ├── setup.sh                 # macOS/Linux setup script
│   ├── setup.bat                # Windows setup script
│   └── requirements.txt         # Python dependencies
├── run.sh                       # macOS/Linux run script
├── run.bat                      # Windows run script
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
├── test_images/                 # Generated test images (git-ignored)
└── venv/                        # Virtual environment (git-ignored)
```

## Controls

### Keyboard Shortcuts
- `←/→` (Left/Right): Navigate left image list
- `↑/↓` (Up/Down): Navigate right image list
- `Tab`: Toggle comparison mode
- `Cmd+L` (Mac) / `Ctrl+L` (Windows/Linux): Toggle list layout (top/sides)
- `Cmd+K` (Mac) / `Ctrl+K` (Windows/Linux): Hide/show file lists
- `Cmd+O` (Mac) / `Ctrl+O` (Windows/Linux): Select new directory
- `Cmd+Q` (Mac) / `Ctrl+Q` (Windows/Linux): Quit application

### Zoom Controls (for images with same dimensions)
- `Cmd+0` (Mac) / `Ctrl+0` (Windows/Linux): Reset zoom to fit view
- `Cmd++` (Mac) / `Ctrl++` (Windows/Linux): Zoom in
- `Cmd+-` (Mac) / `Ctrl+-` (Windows/Linux): Zoom out
- `Mouse wheel` / `Trackpad pinch`: Zoom in/out at cursor position
- `Click and drag`: Pan around zoomed images

### Mouse Controls
- **Side-by-Side Mode**: Click and drag to pan when zoomed in
- **Overlay Mode**: 
  - Click and drag divider to adjust overlay position
  - Hold Cmd/Ctrl while dragging to pan instead of moving divider
- **List Selection**: Click on any image name in either list to select it

## Menu Options

### File Menu
- **Select Directory...**: Choose a new directory to load images from
- **Exit**: Close the application

### View Menu
- **Side by Side**: Switch to side-by-side comparison mode
- **Overlay**: Switch to overlay comparison mode with mouse-controlled slider
- **Toggle Mode**: Switch between the two comparison modes
- **Toggle Lists Layout**: Switch between top/bottom and left/right list arrangements
- **Hide/Show Lists**: Toggle file list visibility for distraction-free viewing

### Debug Menu
- **Show Performance Stats**: Display performance metrics and timing information
- **Show Cache Stats**: View image cache statistics and memory usage
- **Clear All Caches**: Reset all caches and performance counters

## Performance Features

### Image Caching
- **LRU Cache**: Automatically caches recently accessed images for faster loading
- **Scaled Image Cache**: Caches scaled versions to avoid repeated scaling operations
- **Memory Management**: Intelligent eviction prevents excessive memory usage
- **Cache Statistics**: Monitor cache hit rates and memory usage through Debug menu

### Performance Monitoring
- **Operation Timing**: Tracks time spent on image loading, scaling, and display operations
- **Memory Tracking**: Basic memory usage monitoring for optimization
- **Statistics Export**: View detailed performance metrics through the Debug menu

## Troubleshooting

### Performance Issues
1. Check cache statistics (Debug > Show Cache Stats)
2. Clear caches if memory usage is high (Debug > Clear All Caches)
3. Monitor performance stats to identify bottlenecks (Debug > Show Performance Stats)

### Image Loading Issues
- Ensure images are under 200MB size limit
- Check that image formats are supported (JPG, PNG, BMP, TIFF, GIF)
- Verify directory permissions and file accessibility

## Large File Handling

The application automatically filters out image files larger than 200MB to prevent Qt memory allocation errors. When such files are found, they are excluded from the file list and a warning is displayed showing the count of ignored files.
