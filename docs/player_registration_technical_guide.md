# SAFA Player Registration - Technical Implementation Guide

**Version**: 1.0  
**Last Updated**: June 19, 2025

## System Architecture

The player registration system is built on the following components:

- **Django Framework**: Core web application framework
- **PostgreSQL Database**: Stores all player and document information
- **Document Validation System**: OCR-based validation for identity documents
- **File Storage**: Local or cloud storage for document files

## Key Models

### Player Model
```python
class Player(Member):
    is_approved = models.BooleanField(default=False)
    has_sa_passport = models.BooleanField(default=False)
    sa_passport_number = models.CharField(max_length=25, blank=True, null=True)
    sa_passport_document = models.FileField(upload_to='sa_passport_documents/', blank=True, null=True)
    sa_passport_expiry_date = models.DateField(blank=True, null=True)
```

### Member Model (Parent class for Player)
```python
class Member(models.Model):
    # Identity fields
    id_document_type = models.CharField(max_length=2, choices=[('ID', 'SA ID'), ('PP', 'Passport')], default='ID')
    id_number = models.CharField(max_length=13, blank=True)
    passport_number = models.CharField(max_length=25, blank=True, null=True)
    
    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    
    # Documents
    profile_picture = models.ImageField(upload_to='member_profiles/', null=True, blank=True)
    id_document = models.FileField(upload_to='documents/member_documents/', null=True, blank=True)
```

## Key Forms

### ClubAdminPlayerRegistrationForm
- Handles new player registration
- Validates ID and passport information
- Performs document validation via OCR
- Generates unique email addresses automatically

### PlayerUpdateForm
- Handles editing existing player information
- Allows updating or adding missing documents
- Validates SA passport information if provided
- Preserves identity information integrity

## Document Validation System

### Components
1. **Dependency Check**: Verifies OCR libraries are available
2. **Format Validation**: Checks document file format and size
3. **Text Extraction**: Uses OCR to extract text from documents
4. **Content Verification**: Validates extracted text against provided information

### Implementation

The document validation system is implemented in `accounts/utils.py`:

```python
def validate_passport_document(passport_document, passport_number, first_name, last_name, dob=None):
    """
    Validates a passport document by extracting and verifying contents.
    Uses OCR to extract text and match against provided player information.
    
    Returns:
        tuple: (is_valid (bool), messages (list))
    """
    # Document format validation
    # OCR text extraction
    # Content verification
```

### Configuration

Document validation can be configured in Django settings:

```python
# Enable/disable document validation
VALIDATE_PASSPORT_DOCUMENTS = True
```

## Player Registration Workflow

1. **Form Submission**:
   - Club admin submits player registration form
   - System validates personal information
   - System performs document format check

2. **ID Processing**:
   - For SA ID: Extract DOB and gender from ID number
   - For passport: Use provided DOB and gender

3. **Document Validation**:
   - If enabled, OCR extracts text from documents
   - System validates document content matches provided information
   - Document is accepted or flagged for manual review

4. **Email Generation**:
   - System generates unique email in format: firstname.lastname@safaconnectadmin.co.za

5. **Player Creation**:
   - Player record created with pending approval status
   - Club registration record created linking player to club

## Compliance Checking

The system performs these compliance checks before allowing approval:

1. **Profile Picture**: Must be uploaded
2. **ID/Passport Document**: Must be uploaded and validated
3. **Personal Information**: All required fields must be complete
4. **POPI Consent**: Required for players under 18

## Error Handling

1. **Validation Errors**: Return user to form with error messages
2. **Document Format Issues**: Block submission until resolved
3. **OCR Validation Warnings**: Accept document but flag for review
4. **Missing Dependencies**: Fall back to basic validation when OCR is unavailable

## Extension Points

To extend the system:

1. **Add New Document Types**: Extend the Player model and registration forms
2. **Enhance Validation**: Modify the validate_passport_document function in utils.py
3. **Additional Compliance Checks**: Update the approve_player view in views.py

## Performance Considerations

1. **Document Storage**: Consider using cloud storage for documents in production
2. **OCR Processing**: OCR is resource-intensive; consider async processing for large files
3. **Caching**: Consider caching validation results to avoid redundant processing

## Security Considerations

1. **Document Storage**: All documents are stored securely with restricted access
2. **Validation Logs**: OCR validation issues are logged but don't include sensitive data
3. **Permission Checks**: All views enforce strict permission checks for accessing player data

## Troubleshooting Common Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| OCR validation fails | Missing OCR dependencies | Install required libraries or disable validation |
| Document upload fails | File too large or wrong format | Check file size limits and acceptable formats |
| Email generation conflicts | Duplicate player names | Email suffix is incremented automatically |
| Approval button not working | Missing compliance requirements | Check player record for missing documents |
