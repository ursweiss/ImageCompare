#!/usr/bin/env python3
"""
Create sample images for testing the Image Compare application.
This script generates some colorful test images in a 'test_images' directory.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_images():
    """Create a set of test images for demonstration"""

    # Create test images directory
    test_dir = "test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # Image dimensions
    width, height = 800, 600

    # Create different types of test images
    images_to_create = [
        ("red_gradient.jpg", create_gradient, (255, 0, 0), (255, 100, 100)),
        ("blue_gradient.jpg", create_gradient, (0, 0, 255), (100, 100, 255)),
        ("green_pattern.png", create_pattern, (0, 255, 0), "circles"),
        ("yellow_pattern.png", create_pattern, (255, 255, 0), "squares"),
        ("rainbow_stripes.jpg", create_stripes, None, "rainbow"),
        ("checkerboard.png", create_checkerboard, (255, 255, 255), (0, 0, 0)),
        ("purple_noise.jpg", create_noise, (128, 0, 128), None),
        ("orange_text.png", create_text_image, (255, 165, 0), "Sample Text"),
    ]

    for filename, func, color1, color2 in images_to_create:
        filepath = os.path.join(test_dir, filename)
        print(f"Creating {filename}...")

        image = func(width, height, color1, color2)
        image.save(filepath, quality=95 if filename.endswith('.jpg') else None)

    print(f"\nCreated {len(images_to_create)} test images in '{test_dir}' directory")
    print("You can now use this directory to test the Image Compare application!")

def create_gradient(width, height, color1, color2):
    """Create a gradient image"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    for x in range(width):
        ratio = x / width
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))

    return image

def create_pattern(width, height, color, pattern_type):
    """Create a pattern image"""
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    if pattern_type == "circles":
        for i in range(0, width, 100):
            for j in range(0, height, 100):
                draw.ellipse([i, j, i+80, j+80], fill=color)
    elif pattern_type == "squares":
        for i in range(0, width, 100):
            for j in range(0, height, 100):
                draw.rectangle([i, j, i+80, j+80], fill=color)

    return image

def create_stripes(width, height, color1, pattern_type):
    """Create striped image"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    if pattern_type == "rainbow":
        colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
                  (0, 0, 255), (75, 0, 130), (148, 0, 211)]
        stripe_height = height // len(colors)

        for i, color in enumerate(colors):
            y = i * stripe_height
            draw.rectangle([0, y, width, y + stripe_height], fill=color)

    return image

def create_checkerboard(width, height, color1, color2):
    """Create checkerboard pattern"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    square_size = 50
    for x in range(0, width, square_size):
        for y in range(0, height, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                color = color1
            else:
                color = color2
            draw.rectangle([x, y, x + square_size, y + square_size], fill=color)

    return image

def create_noise(width, height, base_color, _):
    """Create noisy image"""
    image = Image.new('RGB', (width, height))
    pixels = []

    for _ in range(width * height):
        r = max(0, min(255, base_color[0] + random.randint(-50, 50)))
        g = max(0, min(255, base_color[1] + random.randint(-50, 50)))
        b = max(0, min(255, base_color[2] + random.randint(-50, 50)))
        pixels.append((r, g, b))

    image.putdata(pixels)
    return image

def create_text_image(width, height, bg_color, text):
    """Create image with text"""
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Try to use a larger font, fall back to default if not available
    try:
        font = ImageFont.truetype("Arial.ttf", 72)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
        except:
            font = ImageFont.load_default()

    # Calculate text position for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return image

if __name__ == "__main__":
    create_test_images()
