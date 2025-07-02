#!/usr/bin/env python
"""
Create a clean black SAFA card template without any existing text
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont
from membership_cards.card_generator import SAFACardGenerator

def create_clean_template():
    print("🎨 Creating Clean Black SAFA Template")
    print("=" * 45)
    
    generator = SAFACardGenerator()
    
    # Create a clean black card template
    width = generator.CARD_WIDTH_PX
    height = generator.CARD_HEIGHT_PX
    
    # Create black background
    template = Image.new('RGB', (width, height), (0, 0, 0))  # Pure black
    draw = ImageDraw.Draw(template)
    
    # Add subtle SAFA branding elements (optional)
    # You can customize these or remove them
    
    # Add a subtle gradient or pattern
    for y in range(height):
        # Create a very subtle gradient from black to dark gray
        gray_value = int(5 + (y / height) * 10)  # Very subtle
        color = (gray_value, gray_value, gray_value)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Add corner decorations (optional)
    corner_color = (20, 20, 20)  # Very dark gray
    
    # Top left corner decoration
    draw.rectangle([0, 0, 100, 3], fill=corner_color)
    draw.rectangle([0, 0, 3, 100], fill=corner_color)
    
    # Top right corner decoration
    draw.rectangle([width-100, 0, width, 3], fill=corner_color)
    draw.rectangle([width-3, 0, width, 100], fill=corner_color)
    
    # Bottom left corner decoration
    draw.rectangle([0, height-3, 100, height], fill=corner_color)
    draw.rectangle([0, height-100, 3, height], fill=corner_color)
    
    # Bottom right corner decoration
    draw.rectangle([width-100, height-3, width, height], fill=corner_color)
    draw.rectangle([width-3, height-100, width, height], fill=corner_color)
    
    # Add subtle SAFA logo area (top center)
    logo_area_width = 200
    logo_area_height = 60
    logo_x = (width - logo_area_width) // 2
    logo_y = 30
    
    # Create a very subtle rectangle for logo area
    draw.rectangle([logo_x, logo_y, logo_x + logo_area_width, logo_y + logo_area_height], 
                  outline=(30, 30, 30), width=1)
    
    # Add "SAFA" text in the logo area (very subtle)
    try:
        # Try to load a font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add subtle SAFA text
    safa_text = "SOUTH AFRICAN FOOTBALL ASSOCIATION"
    text_bbox = draw.textbbox((0, 0), safa_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = logo_y + 20
    
    draw.text((text_x, text_y), safa_text, fill=(40, 40, 40), font=font)  # Very dark gray
    
    # Save the clean template
    clean_template_path = os.path.join("media", "card_templates", "front", "clean_safa_template.jpg")
    os.makedirs(os.path.dirname(clean_template_path), exist_ok=True)
    template.save(clean_template_path, "JPEG", quality=95)
    
    print(f"✅ Clean template created: {clean_template_path}")
    
    # Also save as PNG for better quality
    png_path = clean_template_path.replace('.jpg', '.png')
    template.save(png_path, "PNG")
    print(f"✅ PNG version saved: {png_path}")
    
    return clean_template_path

def update_generator_to_use_clean_template():
    """Update the card generator to use the clean template"""
    clean_template_path = create_clean_template()
    
    print("\n🔧 To use the clean template:")
    print("1. Backup your current template:")
    print("   - Copy safamembership.jpg to safamembership_backup.jpg")
    print("\n2. Replace with clean template:")
    print(f"   - Copy {clean_template_path}")
    print("   - Rename to safamembership.jpg")
    print("\n3. Or I can do this automatically for you...")
    
    # Backup current template
    current_template = os.path.join("media", "card_templates", "front", "safamembership.jpg")
    backup_template = os.path.join("media", "card_templates", "front", "safamembership_backup.jpg")
    
    if os.path.exists(current_template):
        # Create backup
        import shutil
        shutil.copy2(current_template, backup_template)
        print(f"✅ Backup created: {backup_template}")
        
        # Replace with clean template
        shutil.copy2(clean_template_path, current_template)
        print(f"✅ Clean template installed: {current_template}")
        
        return True
    
    return False

if __name__ == "__main__":
    success = update_generator_to_use_clean_template()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("✅ Your original template is backed up")
        print("✅ Clean black template is now active")
        print("✅ No existing text will show through")
        print("\nNow run: python generate_clean_card.py")
    else:
        print("\n⚠️  Manual setup needed - see instructions above")
