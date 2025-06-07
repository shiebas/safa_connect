import base64
from io import BytesIO
import qrcode
from django.conf import settings
import json

def generate_qr_code(data, size=200):
    """
    Generate a QR code from the provided data.
    
    Args:
        data: Dictionary or string data to encode in the QR code
        size: Size of the QR code in pixels
    
    Returns:
        A base64 encoded string that can be embedded in HTML
    """
    try:
        # Convert data to JSON string if it's a dictionary
        if isinstance(data, dict):
            qr_data = json.dumps(data)
        else:
            qr_data = str(data)
            
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        # Add data to QR code
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image to a BytesIO object
        buffer = BytesIO()
        img.save(buffer)
        
        # Encode the image as base64
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    except ImportError:
        # If qrcode is not installed
        return None
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating QR code: {str(e)}")
        return None

def get_member_qr_data(member):
    """
    Prepare member data for QR code generation.
    
    Args:
        member: Member model instance
        
    Returns:
        Dictionary with member information for QR code
    """
    data = {
        'id': str(member.id),
        'safa_id': member.safa_id or '',
        'fifa_id': member.fifa_id or '',
        'name': f"{member.first_name} {member.last_name}",
        'dob': member.date_of_birth.isoformat() if member.date_of_birth else '',
        'role': member.role,
        'status': member.status,
    }
    
    if hasattr(member, 'club') and member.club:
        data['club'] = member.club.name
    
    return data

def get_club_qr_data(club):
    """
    Prepare club data for QR code generation.
    
    Args:
        club: Club model instance
        
    Returns:
        Dictionary with club information for QR code
    """
    data = {
        'id': str(club.id),
        'safa_id': club.safa_id if hasattr(club, 'safa_id') else '',
        'name': club.name,
        'region': club.region.name if hasattr(club, 'region') and club.region else '',
        'province': club.province.name if hasattr(club, 'province') and club.province else '',
    }
    
    return data
