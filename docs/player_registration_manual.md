# SAFA Player Registration Manual

**Version**: 1.0  
**Last Updated**: June 19, 2025  
**Author**: SAFA Technical Team

## Table of Contents

1. [Introduction](#introduction)
2. [Registration Process Overview](#registration-process-overview)
3. [Club Administrator Guide](#club-administrator-guide)
   - [Adding New Players](#adding-new-players)
   - [Document Requirements](#document-requirements)
   - [Player Approval Workflow](#player-approval-workflow)
   - [Editing Player Information](#editing-player-information)
4. [Document Validation System](#document-validation-system)
   - [How Document Validation Works](#how-document-validation-works)
   - [Handling Validation Issues](#handling-validation-issues)
5. [Compliance Requirements](#compliance-requirements)
6. [FAQ](#faq)
7. [Technical Reference](#technical-reference)

## Introduction

This manual provides comprehensive guidance for the SAFA player registration system, designed for club administrators and technical staff. The system ensures proper validation of player identities, maintains compliance with federation requirements, and streamlines the registration process.

## Registration Process Overview

The SAFA player registration process follows these main steps:

1. **Initial Registration**: Club administrators register players using either South African ID or passport information
2. **Document Verification**: Submitted ID and passport documents undergo automated validation
3. **Compliance Check**: System verifies all required information and documents are provided
4. **Approval**: Club administrators approve players once all compliance requirements are met
5. **Card Issuance**: Upon approval, players receive their membership cards

## Club Administrator Guide

### Adding New Players

To add a new player to your club:

1. Log in to your Club Administrator account
2. Navigate to the Dashboard
3. Click "Add Player"
4. Choose the appropriate identification method:
   - **South African ID**: Enter the 13-digit ID number which will auto-populate date of birth and gender
   - **Passport**: Enter passport number, date of birth, and gender manually
5. Complete all required personal information fields
6. Upload profile photo (required) and identity document (required)
7. If applicable, provide optional SA passport information
8. Complete address and contact information
9. Submit the registration form

**Note**: For players with SA ID, you have an option to also register their South African passport if they have one. This is optional but useful for international travel purposes.

### Document Requirements

The following documents are required for player registration:

1. **Profile Picture**:
   - Clear, recent front-facing photo
   - Neutral background
   - Passport-style composition (head and shoulders)
   - File formats: JPG, JPEG, PNG
   - Maximum size: 5MB

2. **Identity Document**:
   - For South African citizens: Copy of ID document (both sides)
   - For non-South African citizens: Copy of passport information page
   - File formats: PDF, JPG, JPEG, PNG
   - Maximum size: 10MB
   - Must clearly show name, ID/passport number, and date of birth

3. **South African Passport (Optional for SA citizens)**:
   - Copy of passport information page
   - File formats: PDF, JPG, JPEG, PNG
   - Maximum size: 10MB

### Player Approval Workflow

Once a player is registered, they must be approved before becoming an active member:

1. Navigate to "Player Approval List" on your dashboard
2. Select a player to view their details
3. Verify all information is correct and complete
4. Check that all required documents are uploaded and valid
5. Click "Approve Player" to complete the process

**Important**: Players cannot be approved until they have both a profile picture and valid ID/passport document uploaded.

### Editing Player Information

To edit an existing player's information:

1. Navigate to "Player Approval List" on your dashboard
2. Find the player and click "View" or "Edit"
3. Update any information as needed
4. Upload or replace documents if required
5. Save the changes

## Document Validation System

### How Document Validation Works

The SAFA registration system includes an advanced document validation feature that:

1. **Validates Format**: Ensures documents are in the correct format and size
2. **Performs OCR (Optical Character Recognition)**: Scans documents to extract text
3. **Verifies Content**: Confirms the document contains the player's:
   - Full name (first and last name)
   - ID or passport number
   - Date of birth (where applicable)

This validation helps prevent fraud and ensures the submitted documents match the registration information.

### Handling Validation Issues

During the document validation process, you may encounter these scenarios:

1. **Successful Validation**: Document passes all checks and is accepted
2. **Format Errors**: Document is in an unsupported format or exceeds size limits
3. **Content Validation Warnings**: System cannot verify all required information in the document

If you receive validation warnings:
- The document will still be accepted, but flagged for manual verification
- Review the document to ensure it matches the player's information
- If the document appears valid, you may proceed with the registration
- For persistent issues, try re-uploading a clearer version of the document

## Compliance Requirements

For a player to be fully compliant and eligible for approval, they must have:

1. A complete profile with all required fields filled in
2. A valid profile picture uploaded
3. A valid ID document (South African ID) or passport document uploaded
4. POPI Act consent (especially important for junior players under 18)

The system visually displays compliance status on the player detail page, showing which requirements have been met and which are still pending.

## FAQ

**Q: Can I register a player without an ID or passport document?**  
A: No, either a South African ID or passport document is required for registration.

**Q: What if OCR validation fails but the document is legitimate?**  
A: The system will still accept the document but flag it for manual verification. You can proceed with registration as long as you've verified the document is valid.

**Q: Can I edit a player's ID number after registration?**  
A: No, ID and passport numbers cannot be edited after registration to prevent identity switching. If there was an error, a new registration is required.

**Q: Do junior players require additional documentation?**  
A: Junior players (under 18) require POPI Act consent, but the registration process is otherwise the same.

**Q: What happens if a player has both a South African ID and a passport?**  
A: Register them with their South African ID as the primary document, then add their passport information in the optional SA passport section.

## Technical Reference

The player registration system utilizes the following technologies for document validation:

- **PyMuPDF**: For PDF document processing
- **Tesseract OCR**: For optical character recognition
- **PIL/Pillow**: For image processing

System administrators can configure document validation settings in the Django settings file:

```python
# Enable/disable document validation
VALIDATE_PASSPORT_DOCUMENTS = True  # Set to False to disable validation
```

For technical support, contact the SAFA technical team at tech-support@safaconnect.co.za
