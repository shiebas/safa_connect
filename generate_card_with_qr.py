from PIL import Image, ImageDraw, ImageFont
import qrcode
import os

# Paths
CARD_PATH = 'media/card_templates/front/safa2.png'
OUTPUT_PATH = 'media/card_templates/front/safa2_with_qr.png'

# Data
qr_data = '1234 5678 9012 3456'  # sample 16-digit code
name = 'Gerald Don'
expiry = 'Expiry 07/26'
safa_id = 'SAFA ID: 511DF'

# Load card template
card = Image.open(CARD_PATH).convert('RGBA')

# Generate QR code
qr = qrcode.make(qr_data)
qr = qr.resize((120, 120))  # adjust size as needed

# Get card and QR code sizes
card_width, card_height = card.size
qr_width, qr_height = qr.size

# Calculate position: 5mm from left and bottom (at 300 DPI, 1mm ≈ 11.81px)
padding = int(5 * 11.81)
qr_x = padding
qr_y = card_height - qr_height - padding

# Paste QR code at new position
card.paste(qr, (qr_x, qr_y))

# Enlarge text and place above QR code, left-aligned
try:
    font = ImageFont.truetype("arial.ttf", 36)
except:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(card)

# Move QR code to left side, 5mm from left and bottom
qr_x = padding
qr_y = card_height - qr_height - padding
card.paste(qr, (qr_x, qr_y))

# Card number: 5mm to the right of QR code, aligned vertically with QR code
card_number_x = qr_x + qr_width + padding  # 5mm from QR code
card_number_y = qr_y + (qr_height // 2) - (font.size // 2)
draw.text((card_number_x, card_number_y), qr_data, fill="white", font=font)

# Name and SAFA ID: 10mm above QR code, left-aligned
vertical_gap_10mm = int(10 * 11.81)
name_y = qr_y - vertical_gap_10mm
safa_id_y = name_y - font.size - 8  # 8px gap above name
draw.text((qr_x, safa_id_y), safa_id, fill="white", font=font)
draw.text((qr_x, name_y), name, fill="white", font=font)

# Expiry: centered horizontally, 5mm from bottom, with semicolon after value
expiry_label = 'Expiry: 07/26;'
expiry_text_width = draw.textbbox((0,0), expiry_label, font=font)[2]
expiry_x = (card_width - expiry_text_width) // 2
expiry_y = card_height - padding
draw.text((expiry_x, expiry_y), expiry_label, fill="white", font=font)

# Save result
card.save(OUTPUT_PATH)
print(f"Card with QR and details saved to {OUTPUT_PATH}")
