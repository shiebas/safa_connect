"""
Facial verification system for tournament registration
Compares live photos against stored reference photos
"""

import cv2
import numpy as np
import face_recognition
from PIL import Image
import io
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)

class FacialVerification:
    """Handles facial verification between live and stored photos"""
    
    def __init__(self):
        self.tolerance = 0.6  # Lower = more strict matching
        self.face_detection_model = 'hog'  # 'hog' or 'cnn' (cnn is more accurate but slower)
    
    def verify_faces(self, live_photo_path, stored_photo_path=None, stored_photo_data=None):
        """
        Verify if the live photo matches a stored photo
        
        Args:
            live_photo_path: Path to the live photo file
            stored_photo_path: Path to stored photo file (optional)
            stored_photo_data: Base64 encoded photo data (optional)
        
        Returns:
            dict: {
                'verified': bool,
                'confidence': float (0-1),
                'face_detected_live': bool,
                'face_detected_stored': bool,
                'error': str (if any)
            }
        """
        try:
            # Load and process live photo
            live_encoding = self._get_face_encoding(live_photo_path)
            if live_encoding is None:
                return {
                    'verified': False,
                    'confidence': 0.0,
                    'face_detected_live': False,
                    'face_detected_stored': False,
                    'error': 'No face detected in live photo'
                }
            
            # Load and process stored photo
            if stored_photo_data:
                stored_encoding = self._get_face_encoding_from_data(stored_photo_data)
            elif stored_photo_path:
                stored_encoding = self._get_face_encoding(stored_photo_path)
            else:
                return {
                    'verified': False,
                    'confidence': 0.0,
                    'face_detected_live': True,
                    'face_detected_stored': False,
                    'error': 'No stored photo provided for comparison'
                }
            
            if stored_encoding is None:
                return {
                    'verified': False,
                    'confidence': 0.0,
                    'face_detected_live': True,
                    'face_detected_stored': False,
                    'error': 'No face detected in stored photo'
                }
            
            # Compare faces
            face_distance = face_recognition.face_distance([stored_encoding], live_encoding)[0]
            confidence = max(0, 1 - face_distance)  # Convert distance to confidence
            verified = face_distance <= self.tolerance
            
            return {
                'verified': verified,
                'confidence': confidence,
                'face_detected_live': True,
                'face_detected_stored': True,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Facial verification error: {str(e)}")
            return {
                'verified': False,
                'confidence': 0.0,
                'face_detected_live': False,
                'face_detected_stored': False,
                'error': f'Verification failed: {str(e)}'
            }
    
    def _get_face_encoding(self, image_path):
        """Extract face encoding from image file"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(
                image, 
                model=self.face_detection_model
            )
            
            if not face_locations:
                return None
            
            # Get face encodings (use first face if multiple detected)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                return face_encodings[0]  # Return first face encoding
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting face encoding from {image_path}: {str(e)}")
            return None
    
    def _get_face_encoding_from_data(self, image_data):
        """Extract face encoding from base64 image data"""
        try:
            # Decode base64 data
            if isinstance(image_data, str):
                if image_data.startswith('data:image'):
                    # Remove data URL prefix
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(pil_image)
            
            # Find face locations
            face_locations = face_recognition.face_locations(
                image_array, 
                model=self.face_detection_model
            )
            
            if not face_locations:
                return None
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            if face_encodings:
                return face_encodings[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting face encoding from image data: {str(e)}")
            return None
    
    def detect_faces(self, image_path):
        """Detect if image contains faces"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(
                image, 
                model=self.face_detection_model
            )
            return len(face_locations) > 0, len(face_locations)
        except Exception as e:
            logger.error(f"Error detecting faces in {image_path}: {str(e)}")
            return False, 0
    
    def get_face_quality_score(self, image_path):
        """Get a quality score for the face in the image"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(
                image, 
                model=self.face_detection_model
            )
            
            if not face_locations:
                return 0.0
            
            # Calculate quality based on face size and position
            face_location = face_locations[0]  # Use first face
            top, right, bottom, left = face_location
            
            # Calculate face area
            face_area = (bottom - top) * (right - left)
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area
            
            # Calculate position score (face should be centered)
            center_x = (left + right) / 2
            center_y = (top + bottom) / 2
            image_center_x = image.shape[1] / 2
            image_center_y = image.shape[0] / 2
            
            position_score = 1 - (
                abs(center_x - image_center_x) / image_center_x +
                abs(center_y - image_center_y) / image_center_y
            ) / 2
            
            # Combine scores
            quality_score = (face_ratio * 0.7 + position_score * 0.3)
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating face quality for {image_path}: {str(e)}")
            return 0.0

# Global instance
facial_verifier = FacialVerification()



