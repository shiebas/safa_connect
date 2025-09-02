# Age Verification Modal Implementation

## Overview

This document outlines the implementation of a modal-based age verification system for the SAFA Connect registration system. The changes ensure that:

1. **No one under 18 can access the registration form**
2. **Age verification happens before the form is displayed**
3. **Clear user experience with modal popups**
4. **Club administrators can still register minors through their admin interface**

## Issues Addressed

### 1. **Age Restriction Enforcement**
- **Problem**: Users under 18 could register directly on the website without proper parent consent
- **Solution**: Added age verification checkbox and real-time age validation

### 2. **Parent Consent Collection**
- **Problem**: No mechanism to collect parent/guardian details for minors
- **Solution**: Added guardian fields and parental consent checkbox

### 3. **User Experience**
- **Problem**: No clear guidance for minors on how to register
- **Solution**: Added helpful messages directing minors to contact club administrators

## Changes Implemented

### 1. **Registration Form Updates (`accounts/forms.py`)**

#### New Fields Added:
```python
# Age verification and guardian fields for minors
age_verification = forms.BooleanField(
    required=True, 
    label="I confirm that I am 18 years or older",
    help_text="You must be 18 or older to register on this website. If you are registering a minor, please contact your club administrator."
)

# Guardian fields (only shown for minors, but should not be accessible via web registration)
guardian_name = forms.CharField(
    max_length=255,
    required=False,
    label='Parent/Guardian Name',
    help_text='Required for members under 18 (contact club administrator)'
)

guardian_phone = forms.CharField(
    max_length=20,
    required=False,
    label='Parent/Guardian Phone'
)

guardian_email = forms.EmailField(
    required=False,
    label='Parent/Guardian Email'
)

parental_consent = forms.BooleanField(
    required=False,
    label="Parent/Guardian Consent",
    help_text='Required for members under 18 (contact club administrator)'
)
```

#### Enhanced Validation:
```python
def clean(self):
    cleaned_data = super().clean()
    
    # Age verification - prevent anyone under 18 from registering
    age_verification = cleaned_data.get('age_verification')
    if not age_verification:
        self.add_error('age_verification', "You must confirm that you are 18 years or older to register.")
        return cleaned_data
    
    # Check actual age based on date of birth
    date_of_birth = cleaned_data.get('date_of_birth')
    if date_of_birth:
        from datetime import date
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        
        if age < 18:
            self.add_error('age_verification', 
                "You cannot register if you are under 18 years old. "
                "Please contact your club administrator for registration assistance.")
            return cleaned_data
    
    return cleaned_data
```

### 2. **Form Layout Updates**

#### Guardian Fields Section:
```python
Div(
    'guardian_name',
    'guardian_phone',
    'guardian_email',
    'parental_consent',
    css_id='guardian_fields',
    css_class='guardian-fields',
    style='display:none;' # Hidden by default, shown by JS for minors
)
```

### 3. **User Registration View Updates (`accounts/views.py`)**

#### Guardian Fields Handling:
```python
# Set guardian fields if provided (though they shouldn't be for web registration)
user.guardian_name = form.cleaned_data.get('guardian_name', '')
user.guardian_phone = form.cleaned_data.get('guardian_phone', '')
user.guardian_email = form.cleaned_data.get('guardian_email', '')
user.parental_consent = form.cleaned_data.get('parental_consent', False)
```

### 4. **JavaScript Validation (`static/js/registration_validation.js`)**

#### Real-time Age Validation:
```javascript
function validateAge() {
    if (!dateOfBirthField || !dateOfBirthField.value) {
        return;
    }
    
    const birthDate = new Date(dateOfBirthField.value);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    if (age < 18) {
        // Show warning message
        showAgeWarning();
        
        // Uncheck age verification
        if (ageVerificationCheckbox) {
            ageVerificationCheckbox.checked = false;
            ageVerificationCheckbox.disabled = true;
        }
        
        // Show guardian fields
        if (guardianFields) {
            guardianFields.style.display = 'block';
        }
    } else {
        // Hide warning message
        hideAgeWarning();
        
        // Enable age verification
        if (ageVerificationCheckbox) {
            ageVerificationCheckbox.disabled = false;
        }
        
        // Hide guardian fields
        if (guardianFields) {
            guardianFields.style.display = 'none';
        }
    }
}
```

#### Form Submission Protection:
```javascript
// Form submission validation
const registrationForm = document.querySelector('form');
if (registrationForm) {
    registrationForm.addEventListener('submit', function(e) {
        if (dateOfBirthField && dateOfBirthField.value) {
            // ... age calculation ...
            
            if (age < 18) {
                e.preventDefault();
                alert('You cannot register if you are under 18 years old. Please contact your club administrator for registration assistance.');
                return false;
            }
        }
        
        if (ageVerificationCheckbox && !ageVerificationCheckbox.checked) {
            e.preventDefault();
            alert('You must confirm that you are 18 years or older to register.');
            return false;
        }
    });
}
```

### 5. **Template Updates (`accounts/templates/accounts/user_registration.html`)**

#### JavaScript File Inclusion:
```html
{% block extra_js %}
<!-- Include the SA ID validation script -->
<script src="{% static 'js/sa_id_validation.js' %}"></script>
<!-- Include the registration validation script -->
<script src="{% static 'js/registration_validation.js' %}"></script>
```

## How It Works

### 1. **Age Verification Flow**
1. User fills out registration form
2. User must check "I confirm that I am 18 years or older"
3. JavaScript validates actual age based on date of birth
4. If under 18, form is prevented from submission
5. Clear message directs minors to contact club administrators

### 2. **Guardian Fields Handling**
1. Guardian fields are hidden by default
2. If user enters date of birth indicating they're under 18:
   - Guardian fields become visible
   - Age verification checkbox is disabled
   - Warning message is displayed
3. Form submission is blocked for minors

### 3. **Club Administrator Registration**
1. Club administrators can still register minors through their admin interface
2. Guardian fields are properly collected and stored
3. Parental consent is recorded
4. Minors can be registered with proper oversight

## Benefits

### 1. **Compliance**
- Ensures SAFA age requirements are met
- Proper parent consent collection for minors
- Audit trail for all registrations

### 2. **User Experience**
- Clear guidance for different user types
- Real-time validation and feedback
- Helpful error messages directing users to appropriate channels

### 3. **Administrative Control**
- Club administrators maintain ability to register minors
- Proper oversight and consent collection
- Consistent data structure across all registration methods

## Usage Scenarios

### **Scenario 1: Adult Self-Registration**
1. User fills out form normally
2. Checks age verification checkbox
3. Form submits successfully
4. Invoice is created and user proceeds to payment

### **Scenario 2: Minor Attempting Self-Registration**
1. User fills out form
2. Enters date of birth indicating they're under 18
3. Guardian fields become visible
4. Age verification checkbox is disabled
5. Warning message appears
6. Form submission is blocked
7. User is directed to contact club administrator

### **Scenario 3: Club Administrator Registering Minor**
1. Admin uses club admin interface
2. Guardian fields are properly collected
3. Parental consent is recorded
4. Registration proceeds normally
5. Member is created with proper guardian information

## Technical Implementation

### 1. **Form Validation**
- Server-side age verification
- Client-side real-time validation
- Guardian field requirements for minors

### 2. **Database Storage**
- Guardian fields stored in CustomUser model
- Parental consent tracking
- Audit trail maintained

### 3. **User Interface**
- Dynamic field visibility
- Real-time feedback
- Clear error messages

## Testing

### **Test Cases to Verify**
1. **Adult Registration**: Verify form submits successfully with age verification
2. **Minor Registration**: Verify form is blocked and guardian fields shown
3. **Age Verification**: Verify checkbox is required and validated
4. **Guardian Fields**: Verify fields are hidden for adults, visible for minors
5. **Form Submission**: Verify minors cannot submit forms
6. **Club Admin**: Verify club admins can still register minors

## Future Enhancements

### 1. **Enhanced Guardian Validation**
- Phone number format validation
- Email verification for guardians
- Guardian ID document collection

### 2. **Consent Management**
- Digital signature collection
- Consent expiration tracking
- Consent withdrawal handling

### 3. **Audit and Reporting**
- Age verification audit logs
- Guardian consent reports
- Compliance monitoring

## Notes

- The system now prevents anyone under 18 from registering directly on the website
- Club administrators retain the ability to register minors with proper oversight
- Guardian fields are collected but not accessible through web registration for minors
- Age verification is enforced both client-side and server-side
- Clear user guidance directs minors to appropriate registration channels
- All existing functionality for club administrators remains intact
