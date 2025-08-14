#!/usr/bin/env python
"""
Create a selective text removal solution - keep images, remove only names in middle
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from PIL import Image, ImageDraw
from membership_cards.card_generator import SAFACardGenerator

def create_selective_text_removal():
    print("🎯 Creating Selective Text Removal Solution")
    print("=" * 50)
    
    generator = SAFACardGenerator()
    original_template_path = generator.template_path
    
    if not os.path.exists(original_template_path):
        print(f"❌ Original template not found: {original_template_path}")
        return
    
    # Load original template
    template = Image.open(original_template_path)
    template = template.resize((generator.CARD_WIDTH_PX, generator.CARD_HEIGHT_PX), Image.Resampling.LANCZOS)
    template = template.convert('RGBA')
    
    print(f"✅ Loaded original template: {template.size}")
    
    # Create selective overlay - only cover text areas in the middle
    overlay = Image.new('RGBA', template.size, (0, 0, 0, 0))  # Transparent
    draw = ImageDraw.Draw(overlay)
    
    # Define text areas to cover (middle section where names typically appear)
    # These coordinates target the middle area where text usually appears
    text_areas = [
        # Main name area (center-left of card)
        {
            'area': (50, generator.CARD_HEIGHT_PX - 250, 
                    generator.CARD_WIDTH_PX - 200, generator.CARD_HEIGHT_PX - 50),
            'description': 'Main text area (names, details)'
        },
        # You can add more specific areas if needed
    ]
    
    print(f"📍 Text areas to cover:")
    for i, area_info in enumerate(text_areas):
        area = area_info['area']
        desc = area_info['description']
        print(f"   {i+1}. {desc}: {area}")
        
        # Sample the area to get the background color
        left, top, right, bottom = area
        
        # Sample multiple points to get average background color
        sample_points = [
            (left + 10, top + 10),
            (right - 10, top + 10),
            (left + 10, bottom - 10),
            (right - 10, bottom - 10),
            ((left + right) // 2, (top + bottom) // 2)
        ]
        
        total_r, total_g, total_b = 0, 0, 0
        valid_samples = 0
        
        for x, y in sample_points:
            if 0 <= x < template.width and 0 <= y < template.height:
                pixel = template.getpixel((x, y))
                if len(pixel) >= 3:
                    total_r += pixel[0]
                    total_g += pixel[1]
                    total_b += pixel[2]
                    valid_samples += 1
        
        if valid_samples > 0:
            avg_r = total_r // valid_samples
            avg_g = total_g // valid_samples
            avg_b = total_b // valid_samples
            background_color = (avg_r, avg_g, avg_b, 255)
        else:
            background_color = (0, 0, 0, 255)  # Default to black
        
        print(f"      Background color: {background_color}")
        
        # Draw rectangle over text area with matching background
        draw.rectangle(area, fill=background_color)
    
    # Composite the selective overlay
    result = Image.alpha_composite(template, overlay)
    
    # Save the selectively edited template
    selective_template_path = os.path.join("media", "card_templates", "front", "selective_safa_template.jpg")
    result.save(selective_template_path, "JPEG", quality=95)
    print(f"✅ Selective template saved: {selective_template_path}")
    
    # Also save as PNG
    png_path = selective_template_path.replace('.jpg', '.png')
    result.save(png_path, "PNG")
    print(f"✅ PNG version saved: {png_path}")
    
    return selective_template_path

def show_areas_for_manual_editing():
    """Show the user exactly which areas need manual editing"""
    print("\n🛠️  For Manual Editing with GIMP/Paint.NET:")
    print("=" * 50)
    
    generator = SAFACardGenerator()
    
    print("📐 Card dimensions:")
    print(f"   Width: {generator.CARD_WIDTH_PX} pixels")
    print(f"   Height: {generator.CARD_HEIGHT_PX} pixels")
    
    print("\n🎯 Areas to edit (remove text only):")
    print("   1. Main text area:")
    print(f"      - X: 50 to {generator.CARD_WIDTH_PX - 200}")
    print(f"      - Y: {generator.CARD_HEIGHT_PX - 250} to {generator.CARD_HEIGHT_PX - 50}")
    print("      - This covers the middle section where names appear")
    
    print("\n🔧 Editing instructions:")
    print("   1. Open your template in GIMP or Paint.NET")
    print("   2. Use Clone Tool or Healing Tool")
    print("   3. Sample nearby background areas")
    print("   4. Paint over the text areas to match background")
    print("   5. Keep all images, logos, borders intact")
    print("   6. Save as PNG for best quality")

def create_visual_guide():
    """Create a visual guide showing which areas will be covered"""
    generator = SAFACardGenerator()
    
    # Load template
    template = Image.open(generator.template_path)
    template = template.resize((generator.CARD_WIDTH_PX, generator.CARD_HEIGHT_PX), Image.Resampling.LANCZOS)
    template = template.convert('RGBA')
    
    # Create guide overlay
    guide_overlay = Image.new('RGBA', template.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(guide_overlay)
    
    # Highlight text areas to be covered
    text_area = (50, generator.CARD_HEIGHT_PX - 250, 
                generator.CARD_WIDTH_PX - 200, generator.CARD_HEIGHT_PX - 50)
    
    # Draw semi-transparent red rectangle over text area
    draw.rectangle(text_area, fill=(255, 0, 0, 100), outline=(255, 0, 0, 255), width=3)
    
    # Add labels
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Label the area
    draw.text((60, generator.CARD_HEIGHT_PX - 260), "TEXT REMOVAL AREA", 
              fill=(255, 255, 255, 255), font=font)
    draw.text((60, generator.CARD_HEIGHT_PX - 240), "(Names will be removed from here)", 
              fill=(255, 255, 255, 255), font=font)
    
    # Composite guide
    guide_image = Image.alpha_composite(template, guide_overlay)
    
    # Save guide
    guide_path = "text_removal_guide.png"
    guide_image.save(guide_path, "PNG")
    print(f"✅ Visual guide created: {guide_path}")
    print("   (Red area shows where text will be removed)")
    
    return guide_path

def main():
    print("🎨 SAFA Template - Selective Text Removal")
    print("=" * 50)
    
    # Create visual guide
    guide_path = create_visual_guide()
    
    # Create selective removal
    selective_path = create_selective_text_removal()
    
    # Show manual editing info
    show_areas_for_manual_editing()
    
    print(f"\n📊 Results:")
    print(f"1. Visual Guide: {guide_path}")
    print(f"2. Auto-edited Template: {selective_path}")
    
    print(f"\n🎯 Next Steps:")
    print("1. Check the visual guide to see the red area")
    print("2. If auto-removal looks good, I can activate it")
    print("3. Or use GIMP/Paint.NET for precise manual editing")

if __name__ == "__main__":
    main()
