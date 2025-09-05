import os
import uuid
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import math

class TeamPhotoGenerator:
    """Generate composite team photos from individual player photos"""
    
    def __init__(self):
        self.base_width = 800
        self.base_height = 600
        self.player_photo_size = (120, 120)
        self.margin = 20
        self.rows = 3
        self.cols = 5
        
    def generate_team_photo(self, team, player_photos=None):
        """
        Generate a composite team photo from individual player photos
        
        Args:
            team: TournamentTeam instance
            player_photos: List of player photo paths (optional, will get from registrations if not provided)
        
        Returns:
            ContentFile: Generated team photo
        """
        try:
            # Get player photos from team registrations if not provided
            if not player_photos:
                player_photos = self._get_player_photos_from_team(team)
            
            if not player_photos:
                # If no player photos, create a placeholder team photo
                return self._create_placeholder_team_photo(team)
            
            # Create the composite image
            composite_image = self._create_composite_image(team, player_photos)
            
            # Save to ContentFile
            img_buffer = BytesIO()
            composite_image.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            filename = f"team_photo_{team.id}_{uuid.uuid4().hex[:8]}.jpg"
            return ContentFile(img_buffer.getvalue(), name=filename)
            
        except Exception as e:
            print(f"Error generating team photo: {e}")
            return self._create_placeholder_team_photo(team)
    
    def _get_player_photos_from_team(self, team):
        """Get player photos from team registrations"""
        player_photos = []
        
        # Get photos from tournament registrations
        registrations = team.registrations.filter(
            verification_status='VERIFIED',
            live_photo__isnull=False
        ).order_by('registered_at')[:15]  # Limit to 15 players
        
        for registration in registrations:
            if registration.live_photo:
                try:
                    # Open and resize the photo
                    photo_path = registration.live_photo.path
                    if os.path.exists(photo_path):
                        player_photos.append(photo_path)
                except Exception as e:
                    print(f"Error processing photo for {registration.full_name}: {e}")
                    continue
        
        return player_photos
    
    def _create_composite_image(self, team, player_photos):
        """Create the composite team photo"""
        # Calculate grid dimensions
        num_photos = len(player_photos)
        if num_photos <= 5:
            cols = num_photos
            rows = 1
        elif num_photos <= 10:
            cols = 5
            rows = 2
        else:
            cols = 5
            rows = 3
        
        # Calculate image dimensions
        img_width = (cols * self.player_photo_size[0]) + ((cols + 1) * self.margin)
        img_height = (rows * self.player_photo_size[1]) + ((rows + 1) * self.margin) + 100  # Extra space for team name
        
        # Create base image with team colors
        try:
            primary_color = team.team_color_primary
            secondary_color = team.team_color_secondary
        except:
            primary_color = '#667eea'
            secondary_color = '#764ba2'
        
        # Create gradient background
        base_image = Image.new('RGB', (img_width, img_height), primary_color)
        draw = ImageDraw.Draw(base_image)
        
        # Add gradient effect
        for y in range(img_height):
            ratio = y / img_height
            r = int(int(primary_color[1:3], 16) * (1 - ratio) + int(secondary_color[1:3], 16) * ratio)
            g = int(int(primary_color[3:5], 16) * (1 - ratio) + int(secondary_color[3:5], 16) * ratio)
            b = int(int(primary_color[5:7], 16) * (1 - ratio) + int(secondary_color[5:7], 16) * ratio)
            draw.line([(0, y), (img_width, y)], fill=(r, g, b))
        
        # Add team name at the top
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            except:
                font = ImageFont.load_default()
        
        team_name = team.name
        team_short = f"({team.short_name})"
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), team_name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (img_width - text_width) // 2
        text_y = 20
        
        # Draw team name
        draw.text((text_x, text_y), team_name, fill='white', font=font)
        
        # Draw team short name
        short_bbox = draw.textbbox((0, 0), team_short, font=font)
        short_width = short_bbox[2] - short_bbox[0]
        short_x = (img_width - short_width) // 2
        short_y = text_y + 45
        
        draw.text((short_x, short_y), team_short, fill='white', font=font)
        
        # Add player photos
        photo_y_start = 100
        for i, photo_path in enumerate(player_photos[:15]):  # Limit to 15 photos
            row = i // cols
            col = i % cols
            
            x = self.margin + (col * (self.player_photo_size[0] + self.margin))
            y = photo_y_start + (row * (self.player_photo_size[1] + self.margin))
            
            try:
                # Open and process player photo
                player_img = Image.open(photo_path)
                player_img = player_img.convert('RGB')
                
                # Resize and crop to square
                player_img = self._resize_and_crop_square(player_img, self.player_photo_size[0])
                
                # Create circular mask
                mask = Image.new('L', self.player_photo_size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, self.player_photo_size[0], self.player_photo_size[1]), fill=255)
                
                # Apply mask to create circular photo
                player_img.putalpha(mask)
                
                # Paste onto base image
                base_image.paste(player_img, (x, y), player_img)
                
            except Exception as e:
                print(f"Error processing player photo {photo_path}: {e}")
                # Draw placeholder circle
                draw.ellipse([x, y, x + self.player_photo_size[0], y + self.player_photo_size[1]], 
                           fill='#cccccc', outline='white', width=3)
                # Draw question mark
                try:
                    placeholder_font = ImageFont.truetype("arial.ttf", 48)
                except:
                    placeholder_font = ImageFont.load_default()
                text_bbox = draw.textbbox((0, 0), "?", font=placeholder_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + (self.player_photo_size[0] - text_width) // 2
                text_y = y + (self.player_photo_size[1] - text_height) // 2
                draw.text((text_x, text_y), "?", fill='white', font=placeholder_font)
        
        return base_image
    
    def _resize_and_crop_square(self, img, size):
        """Resize and crop image to square"""
        # Get the smaller dimension
        width, height = img.size
        min_dim = min(width, height)
        
        # Crop to square from center
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        
        img = img.crop((left, top, right, bottom))
        
        # Resize to target size
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        return img
    
    def _create_placeholder_team_photo(self, team):
        """Create a placeholder team photo when no player photos are available"""
        try:
            # Create a simple placeholder image
            img_width = 400
            img_height = 300
            
            # Create image with team colors
            try:
                primary_color = team.team_color_primary
                secondary_color = team.team_color_secondary
            except:
                primary_color = '#667eea'
                secondary_color = '#764ba2'
            
            # Create gradient background
            img = Image.new('RGB', (img_width, img_height), primary_color)
            draw = ImageDraw.Draw(img)
            
            # Add gradient effect
            for y in range(img_height):
                ratio = y / img_height
                r = int(int(primary_color[1:3], 16) * (1 - ratio) + int(secondary_color[1:3], 16) * ratio)
                g = int(int(primary_color[3:5], 16) * (1 - ratio) + int(secondary_color[5:7], 16) * ratio)
                b = int(int(primary_color[5:7], 16) * (1 - ratio) + int(secondary_color[5:7], 16) * ratio)
                draw.line([(0, y), (img_width, y)], fill=(r, g, b))
            
            # Add team name
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            team_name = team.name
            text_bbox = draw.textbbox((0, 0), team_name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (img_width - text_width) // 2
            text_y = (img_height - 50) // 2
            
            draw.text((text_x, text_y), team_name, fill='white', font=font)
            
            # Add "No Photos Yet" text
            try:
                small_font = ImageFont.truetype("arial.ttf", 24)
            except:
                small_font = ImageFont.load_default()
            
            no_photos_text = "No player photos yet"
            small_bbox = draw.textbbox((0, 0), no_photos_text, font=small_font)
            small_width = small_bbox[2] - small_bbox[0]
            small_x = (img_width - small_width) // 2
            small_y = text_y + 60
            
            draw.text((small_x, small_y), no_photos_text, fill='white', font=small_font)
            
            # Save to ContentFile
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            filename = f"team_placeholder_{team.id}_{uuid.uuid4().hex[:8]}.jpg"
            return ContentFile(img_buffer.getvalue(), name=filename)
            
        except Exception as e:
            print(f"Error creating placeholder team photo: {e}")
            return None

# Global instance
team_photo_generator = TeamPhotoGenerator()


