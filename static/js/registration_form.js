function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateSAIdNumber(idNumber) {
    if (!idNumber || idNumber.length !== 13 || !/^\d{13}$/.test(idNumber)) {
        return { valid: false, message: 'ID number must be exactly 13 digits', details: null };
    }
    
    const year = parseInt(idNumber.substring(0, 2));
    const month = parseInt(idNumber.substring(2, 4));
    const day = parseInt(idNumber.substring(4, 6));
    
    const currentYear = new Date().getFullYear() % 100;
    const fullYear = year > currentYear ? 1900 + year : 2000 + year;
    
    const date = new Date(fullYear, month - 1, day);
    if (date.getFullYear() !== fullYear || date.getMonth() !== month - 1 || date.getDate() !== day) {
        return { valid: false, message: 'Invalid date in ID number', details: null };
    }
    
    const genderDigit = parseInt(idNumber.substring(6, 10));
    const gender = genderDigit >= 5000 ? 'Male' : 'Female';
    
    // Validate checksum
    let total = 0;
    for (let i = 0; i < 12; i++) {
        const digit = parseInt(idNumber[i]);
        if (i % 2 === 0) {
            total += digit;
        } else {
            const doubled = digit * 2;
            total += doubled > 9 ? doubled - 9 : doubled;
        }
    }
    
    const checkDigit = (10 - (total % 10)) % 10;
    if (checkDigit !== parseInt(idNumber[12])) {
        return { valid: false, message: 'Invalid ID number checksum', details: null };
    }
    
    return {
        valid: true,
        message: 'Valid South African ID number',
        details: {
            dateOfBirth: date.toLocaleDateString('en-ZA'),
            gender: gender,
            age: new Date().getFullYear() - fullYear
        }
    };
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Registration form JS loaded');
    
    // Name validation
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');
    
    function validateName(input) {
        const value = input.value;
        const alphabeticOnly = /^[a-zA-Z\s]*$/;
        
        if (!alphabeticOnly.test(value)) {
            input.value = value.replace(/[^a-zA-Z\s]/g, '');
        }
        
        if (value.trim().length < 3 && value.length > 0) {
            input.style.borderColor = 'red';
        } else {
            input.style.borderColor = '';
        }
    }
    
    if (firstNameInput) firstNameInput.addEventListener('input', () => validateName(firstNameInput));
    if (lastNameInput) lastNameInput.addEventListener('input', () => validateName(lastNameInput));
    
    // ID validation on focus AND input
    const idInputs = document.querySelectorAll('input[name="id_number"]');
    let isIdValid = false;
    
    idInputs.forEach(input => {
        // Validate on focus (when user clicks into field)
        input.addEventListener('focus', function() {
            console.log('ID field focused');
            if (this.value.length > 0) {
                validateIdNumberField(this);
            }
        });
        
        // Validate on input (as user types)
        input.addEventListener('input', function() {
            console.log('ID field input:', this.value);
            if (this.value.length > 0) {
                validateIdNumberField(this);
            } else {
                clearValidation(this);
                isIdValid = false;
            }
        });
        
        // Validate on blur (when user leaves field)
        input.addEventListener('blur', function() {
            console.log('ID field blur');
            if (this.value.length > 0) {
                validateIdNumberField(this);
            }
        });
    });
    
    function validateIdNumberField(input) {
        console.log('Validating ID:', input.value);
        const validationDiv = input.parentNode.querySelector('.id-validation') || 
                            (() => {
                                const div = document.createElement('div');
                                div.className = 'id-validation mt-1';
                                input.parentNode.appendChild(div);
                                return div;
                            })();
        
        const result = validateSAIdNumber(input.value);
        if (result.valid) {
            validationDiv.innerHTML = `<small class="text-success">✓ Valid ID: ${result.details.gender}, Age ${result.details.age}</small>`;
            input.style.borderColor = 'green';
            isIdValid = true;
        } else {
            validationDiv.innerHTML = `<small class="text-danger">✗ ${result.message}</small>`;
            input.style.borderColor = 'red';
            isIdValid = false;
        }
    }
    
    function clearValidation(input) {
        const validationDiv = input.parentNode.querySelector('.id-validation');
        if (validationDiv) {
            validationDiv.innerHTML = '';
        }
        input.style.borderColor = '';
    }
    
    // Prevent form submission if ID is invalid
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            console.log('Form submission attempt');
            
            // Check if there's an ID field with a value
            const idField = form.querySelector('input[name="id_number"]');
            if (idField && idField.value.length > 0) {
                console.log('Checking ID validity before submit');
                const result = validateSAIdNumber(idField.value);
                if (!result.valid) {
                    e.preventDefault();
                    alert('Please enter a valid South African ID number before submitting.');
                    idField.focus();
                    return false;
                }
            }
            
            console.log('Form validation passed');
        });
    });
    
    // Document type switching
    const docTypeSelect = document.getElementById('id_id_document_type');
    const idNumberField = document.getElementById('id-number-field');
    const passportField = document.getElementById('passport-field');
    const driverLicenseField = document.getElementById('driver-license-field');
    const otherDocumentField = document.getElementById('other-document-field');
    
    function updateFields() {
        if (!docTypeSelect) return;
        
        const docType = docTypeSelect.value;
        console.log('Document type changed to:', docType);
        
        // Hide all fields
        [idNumberField, passportField, driverLicenseField, otherDocumentField].forEach(field => {
            if (field) field.style.display = 'none';
        });
        
        // Show appropriate field
        if (docType === 'ID' || docType === 'BC') {
            if (idNumberField) {
                idNumberField.style.display = 'block';
                console.log('Showing ID field');
            }
        } else if (docType === 'PP') {
            if (passportField) {
                passportField.style.display = 'block';
                console.log('Showing passport field');
            }
        } else if (docType === 'DL') {
            if (driverLicenseField) {
                driverLicenseField.style.display = 'block';
                console.log('Showing driver license field');
            }
        } else if (docType === 'OT') {
            if (otherDocumentField) {
                otherDocumentField.style.display = 'block';
                console.log('Showing other document field');
            }
        }
    }
    
    if (docTypeSelect) {
        docTypeSelect.addEventListener('change', updateFields);
        updateFields();
    }
});
