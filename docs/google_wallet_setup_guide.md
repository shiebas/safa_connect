# Google Wallet Integration: Setup Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Platform Setup](#google-cloud-platform-setup)
4. [Service Account Configuration](#service-account-configuration)
5. [Django Integration](#django-integration)
6. [Testing Your Implementation](#testing-your-implementation)
7. [Production Considerations](#production-considerations)
8. [Troubleshooting](#troubleshooting)

## Introduction

This guide provides step-by-step instructions for setting up Google Wallet integration with the SAFA Digital Card system. Google Wallet allows members to add their SAFA membership cards to their mobile devices, enabling easy access and improving the overall member experience.

## Prerequisites

Before beginning, ensure you have:

1. Google account with administrative access
2. Access to Google Cloud Platform (GCP)
3. Billing account enabled on GCP (required for API usage)
4. Basic understanding of Django and Python
5. Administrative access to the SAFA website settings

## Google Cloud Platform Setup

### 1. Create a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a name (e.g., "SAFA Digital Wallet")
5. Select an organization if applicable
6. Click "Create"

### 2. Enable Google Wallet API

1. Select your new project from the project dropdown
2. From the navigation menu, go to "APIs & Services" > "Library"
3. Search for "Google Wallet API"
4. Click on the API and then click "Enable"

### 3. Set Up OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you're using Google Workspace)
3. Enter your app information:
   - App name: "SAFA Digital Card"
   - User support email: Your support email
   - Developer contact information: Your contact email
4. Click "Save and Continue"
5. For scopes, add the Google Wallet API scopes
6. Click "Save and Continue"
7. Add test users if needed
8. Click "Save and Continue" to complete the setup

## Service Account Configuration

### 1. Create Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a service account name (e.g., "safa-wallet-service")
4. Add a description (e.g., "Service account for SAFA Google Wallet integration")
5. Click "Create and Continue"
6. For role, select "Google Wallet API" > "Wallet Object Issuer"
7. Click "Continue" and then "Done"

### 2. Create and Download Key

1. Click on your newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Select "JSON" as the key type
5. Click "Create"
6. The key file will download automatically. Keep this file secure!

### 3. Get Issuer ID

1. Go to [Google Pay and Wallet Console](https://pay.google.com/business/console/)
2. Sign in with your Google account
3. Click "Create a new Wallet Object"
4. Choose "Loyalty card" as the object type
5. Your issuer ID will be displayed on the screen
6. Note this number for configuration in your Django settings

## Django Integration

### 1. Move Service Account Key

1. Create a secure directory for credentials:
   ```bash
   mkdir -p /home/shaun/safa_global/credentials
   ```

2. Move the downloaded JSON key file to the credentials directory:
   ```bash
   mv /path/to/downloaded/key.json /home/shaun/safa_global/credentials/google_wallet_key.json
   ```

3. Secure the file:
   ```bash
   chmod 600 /home/shaun/safa_global/credentials/google_wallet_key.json
   ```

### 2. Update Django Settings

Add the following configuration to your `settings.py`:

```python
# Google Wallet Settings
GOOGLE_WALLET_ENABLED = True
GOOGLE_WALLET_ISSUER_ID = 'your-issuer-id'  # Replace with your actual issuer ID
GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL = 'your-service-account@project.iam.gserviceaccount.com'  # Replace with your email
GOOGLE_WALLET_KEY_FILE = os.path.join(BASE_DIR, 'credentials', 'google_wallet_key.json')
```

### 3. Install Required Packages

Add the following to your `requirements.txt` file:

```
google-auth>=2.10.0
google-api-python-client>=2.50.0
google-auth-oauthlib>=1.0.0
```

Then install them:

```bash
pip install -r requirements.txt
```

## Testing Your Implementation

### 1. Test Environment

1. Set up a test issuer ID in your development settings:
   ```python
   if DEBUG:
       GOOGLE_WALLET_ISSUER_ID = '3388000000022222228'  # Test issuer ID
   ```

2. Create a Google Wallet manager test:
   ```python
   from membership_cards.google_wallet import GoogleWalletManager

   def test_wallet_manager():
       wallet_manager = GoogleWalletManager()
       if wallet_manager.is_configured():
           print("Google Wallet is properly configured")
       else:
           print("Google Wallet configuration issues found")
   ```

### 2. Test Card Creation

1. Create a test digital card
2. Generate a JWT token for Google Wallet
3. Verify the save URL opens correctly
4. Add the card to your personal Google Wallet to check appearance

## Production Considerations

### 1. Security Best Practices

1. Ensure the service account key file is not in a web-accessible directory
2. Add the credentials directory to `.gitignore`
3. Consider using environment variables for sensitive information
4. Implement rate limiting on Google Wallet endpoints

### 2. Production Settings

Before going live:

1. Replace the test issuer ID with your production issuer ID
2. Ensure the production service account has limited permissions
3. Set up proper monitoring for API usage and errors
4. Implement error tracking and notifications

### 3. Backup Process

Create a backup process for your Google Wallet credentials:

1. Document the setup process
2. Store credentials backup securely
3. Ensure multiple administrators know how to restore access if needed

## Troubleshooting

### Common Issues and Solutions

1. **API Quota Exceeded**
   - Check your GCP billing account
   - Review API usage limits
   - Consider requesting a quota increase

2. **Authentication Errors**
   - Verify service account key is correct
   - Ensure service account has proper permissions
   - Check that the file path in settings is correct

3. **JWT Token Creation Failures**
   - Verify all required pass fields are present
   - Check for payload formatting issues
   - Ensure class and object IDs follow Google's requirements

4. **Cards Not Appearing in Google Wallet**
   - Verify device compatibility
   - Check that JWT token is properly signed
   - Ensure the save URL is correctly formatted

5. **Server Errors**
   - Check server logs for API-specific error messages
   - Verify network connectivity to Google APIs
   - Test API connectivity from server environment

### Support Resources

1. [Google Wallet API Documentation](https://developers.google.com/wallet)
2. [Google Cloud Support](https://cloud.google.com/support)
3. [Django Documentation](https://docs.djangoproject.com/)
4. SAFA development team: dev-support@safa.org.za

---

*Last Updated: June 18, 2025*
