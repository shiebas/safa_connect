"""
This is a helper script to generate favicon files for the SAFA website.
Run this once to create the necessary favicon files.
"""
import os
from PIL import Image, ImageDraw, ImageFont

# Create the directory if it doesn't exist
os.makedirs(os.path.dirname(__file__), exist_ok=True)

# Colors
SAFA_GREEN = (0, 133, 66)  # SAFA green color
SAFA_YELLOW = (252, 209, 22)  # SAFA yellow color

def create_simple_favicon(size, filename):
    """Create a simple square favicon with SAFA colors and 'S' letter"""
    img = Image.new('RGB', (size, size), SAFA_GREEN)
    draw = ImageDraw.Draw(img)
    
    # Draw a yellow circle in the center
    circle_radius = size // 3
    circle_pos = (size // 2, size // 2)
    draw.ellipse(
        (circle_pos[0] - circle_radius, 
         circle_pos[1] - circle_radius,
         circle_pos[0] + circle_radius,
         circle_pos[1] + circle_radius), 
        fill=SAFA_YELLOW
    )
    
    # Add an 'S' in the center if size is large enough
    if size >= 32:
        try:
            # Try to use a system font, fallback to default
            font = ImageFont.truetype("Arial Bold", size=size // 2)
        except IOError:
            font = ImageFont.load_default()
            
        # Draw the 'S' centered in the yellow circle
        text_width = font.getlength("S") if hasattr(font, 'getlength') else size // 4
        draw.text(
            (circle_pos[0] - text_width // 2, 
             circle_pos[1] - size // 4),
            "S", 
            fill=SAFA_GREEN, 
            font=font
        )
    
    # Save the image
    img.save(os.path.join(os.path.dirname(__file__), filename))
    print(f"Created {filename}")

# Generate different sizes
create_simple_favicon(16, "favicon-16x16.png")
create_simple_favicon(32, "favicon-32x32.png")
create_simple_favicon(180, "apple-touch-icon.png")
create_simple_favicon(192, "android-chrome-192x192.png")
