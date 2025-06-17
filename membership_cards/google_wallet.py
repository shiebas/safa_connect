import json
import time
import uuid
import datetime
from django.conf import settings
import os

# Try to import Google libraries, but don't fail if they're not installed
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError:
    GOOGLE_LIBRARIES_AVAILABLE = False

class GoogleWalletManager:
    """
    Handles creation and management of Google Wallet passes
    """
    
    def __init__(self):
        self.base_url = "https://walletobjects.googleapis.com/walletobjects/v1"
        self.batch_url = "https://walletobjects.googleapis.com/batch"
        self.class_url = f"{self.base_url}/genericClass"
        self.object_url = f"{self.base_url}/genericObject"
        
        # Try to load credentials from settings or environment
        self.credentials = None
        self.service_account_email = getattr(settings, 'GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL', None)
        
        # If Google libraries aren't available, we can't proceed with setup
        if not GOOGLE_LIBRARIES_AVAILABLE:
            return
        
        # Path to service account key
        key_file_path = getattr(settings, 'GOOGLE_WALLET_KEY_FILE', None) 
        
        # This allows for easy development/production switches
        if key_file_path and os.path.exists(key_file_path):
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    key_file_path,
                    scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
                )
            except Exception as e:
                print(f"Error loading Google Wallet credentials: {e}")
                # Credentials will remain None

    def is_configured(self):
        """Check if Google Wallet is properly configured"""
        return GOOGLE_LIBRARIES_AVAILABLE and self.credentials is not None
        
    def get_authorized_session(self):
        """Get an authorized session for API requests"""
        if not self.is_configured():
            raise ValueError("Google Wallet is not configured. Please set up service account credentials.")
        
        return AuthorizedSession(self.credentials)
        
    def create_class(self, issuer_id, class_suffix):
        """Create a pass class (template) for SAFA membership cards"""
        # Form full class ID
        class_id = f"{issuer_id}.{class_suffix}"
        
        # Define pass class data
        generic_class = {
            'id': class_id,
            'classTemplateInfo': {
                'cardTemplateOverride': {
                    'cardRowTemplateInfos': [
                        {
                            'twoItems': {
                                'startItem': {
                                    'firstValue': {
                                        'fields': [
                                            {
                                                'fieldPath': 'object.textModulesData["member_since"]'
                                            }
                                        ]
                                    }
                                },
                                'endItem': {
                                    'firstValue': {
                                        'fields': [
                                            {
                                                'fieldPath': 'object.textModulesData["expires"]'
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            'imageModulesData': [
                {
                    'mainImage': {
                        'sourceUri': {
                            'uri': f"{settings.BASE_URL}/static/images/safa_logo_small.png"
                        },
                        'contentDescription': {
                            'defaultValue': {
                                'language': 'en-US',
                                'value': 'SAFA Logo'
                            }
                        }
                    }
                }
            ],
            'textModulesData': [
                {
                    'header': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'South African Football Association'
                        }
                    },
                    'body': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'Official Membership Card'
                        }
                    }
                }
            ],
            'linksModuleData': {
                'uris': [
                    {
                        'uri': 'https://www.safa.net/',
                        'description': 'SAFA Website'
                    },
                    {
                        'uri': f"{settings.BASE_URL}/membership-cards/verify/",
                        'description': 'Verify Card'
                    }
                ]
            },
            'hexBackgroundColor': '#006633',
            'heroImage': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/default_logo.png"
                }
            }
        }
        
        try:
            session = self.get_authorized_session()
            response = session.post(
                self.class_url, 
                json=generic_class
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # If class already exists, try to get it
                if response.status_code == 409:  # Conflict - resource already exists
                    get_response = session.get(f"{self.class_url}/{class_id}")
                    if get_response.status_code == 200:
                        return get_response.json()
                
                raise Exception(f"Error creating pass class: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error creating pass class: {str(e)}")
    
    def create_wallet_object(self, issuer_id, class_suffix, digital_card):
        """Create a Google Wallet pass object for a specific member"""
        # Get user from digital card
        user = digital_card.user
        
        # Form full class and object IDs
        class_id = f"{issuer_id}.{class_suffix}"
        object_id = f"{class_id}.{user.safa_id}_{int(time.time())}"
        
        # Format dates
        issued_date = digital_card.issued_date.strftime("%Y-%m-%d")
        expires_date = digital_card.expires_date.strftime("%Y-%m-%d")
        
        # Create the pass object
        generic_object = {
            'id': object_id,
            'classId': class_id,
            'genericType': 'GENERIC_TYPE_UNSPECIFIED',
            'hexBackgroundColor': '#006633',
            'logo': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/safa_logo_small.png"
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'SAFA Logo'
                    }
                }
            },
            'cardTitle': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': 'SAFA Membership Card'
                }
            },
            'header': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': f"{user.get_full_name()}"
                }
            },
            'subheader': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': f"SAFA ID: {user.safa_id}"
                }
            },
            'textModulesData': [
                {
                    'id': 'member_since',
                    'header': 'Member Since',
                    'body': issued_date
                },
                {
                    'id': 'expires',
                    'header': 'Expires',
                    'body': expires_date
                },
                {
                    'id': 'card_number',
                    'header': 'Card Number',
                    'body': digital_card.card_number
                },
                {
                    'id': 'membership_type',
                    'header': 'Type',
                    'body': user.get_role_display() if hasattr(user, 'get_role_display') else 'Member'
                }
            ],
            'barcode': {
                'type': 'QR_CODE',
                'value': digital_card.qr_code_data,
                'alternateText': digital_card.card_number
            },
            'heroImage': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/default_logo.png"
                }
            },
            'state': 'ACTIVE' if digital_card.status == 'ACTIVE' else 'INACTIVE'
        }
        
        try:
            session = self.get_authorized_session()
            response = session.post(
                self.object_url,
                json=generic_object
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # If object already exists, try to update it
                if response.status_code == 409:  # Conflict
                    # Try to get the existing object
                    get_response = session.get(f"{self.object_url}/{object_id}")
                    if get_response.status_code == 200:
                        # Update the existing object
                        patch_response = session.patch(
                            f"{self.object_url}/{object_id}",
                            json=generic_object
                        )
                        if patch_response.status_code == 200:
                            return patch_response.json()
                
                raise Exception(f"Error creating wallet object: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error creating wallet object: {str(e)}")
    
    def create_jwt_token(self, issuer_id, class_suffix, digital_card):
        """
        Create a signed JWT that can be used to add a pass to Google Wallet
        """
        if not self.is_configured():
            return None
        
        # Get user from digital card
        user = digital_card.user
        
        try:
            # Create class and object first to ensure they exist
            self.create_class(issuer_id, class_suffix)
            wallet_object = self.create_wallet_object(issuer_id, class_suffix, digital_card)
            
            # Form full class and object IDs
            class_id = f"{issuer_id}.{class_suffix}"
            object_id = f"{class_id}.{user.safa_id}_{int(time.time())}"
            
            # Create the JWT payload
            payload = {
                'iss': self.service_account_email,
                'aud': 'google',
                'typ': 'savetowallet',
                'iat': int(time.time()),
                'payload': {
                    'genericObjects': [
                        {
                            'id': object_id,
                            'classId': class_id
                        }
                    ]
                }
            }
            
            # Sign the JWT
            token = self.credentials.sign_jwt(payload, expiry=None)
            
            return token
            
        except Exception as e:
            print(f"Error creating JWT token: {str(e)}")
            return None
