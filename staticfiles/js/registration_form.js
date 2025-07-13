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

    // Validate checksum using Luhn algorithm for South African ID
    let oddSum = 0;
    let evenDigits = "";

    // Process all digits except the check digit
    for (let i = 0; i < idNumber.length - 1; i++) {
        const digit = parseInt(idNumber[i]);
        if (i % 2 === 0) {  // Odd position (1-indexed)
            oddSum += digit;
        } else {  // Even position (1-indexed)
            evenDigits += digit;
        }
    }

    // Double the even digits as a single number and sum its digits
    const doubledEven = parseInt(evenDigits) * 2;
    const evenSum = doubledEven.toString().split('').reduce((sum, digit) => sum + parseInt(digit), 0);

    // Calculate the total and check digit
    const total = oddSum + evenSum;
    const checkDigit = (10 - (total % 10)) % 10;

    // Compare with the actual check digit
    if (checkDigit !== parseInt(idNumber[12])) {
        return { valid: false, message: "Invalid ID number checksum.", details: null };
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

// [Previous validation functions remain exactly the same...]

// [Keep all existing validation functions...]

// [Previous validation functions remain exactly the same...]

document.addEventListener('DOMContentLoaded', function() {
    console.log('Registration form JS loaded');

    // Name validation (unchanged)
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

    // Enhanced ID validation to work with all document types
    function setupDocumentValidation() {
        const docTypeSelect = document.querySelector('select[name="id_document_type"]');
        const idInput = document.querySelector('input[name="id_number"]');
        const passportInput = document.querySelector('input[name="passport_number"]');
        const driverLicenseInput = document.querySelector('input[name="driver_license_number"]');
        const otherDocInput = document.querySelector('input[name="id_number_other"]');

        function validateCurrentField() {
            const activeField = getActiveDocumentField();
            if (!activeField) return;

            if (activeField.name === 'id_number') {
                validateIdNumberField(activeField);
            } else {
                // Basic validation for other document types
                if (activeField.value.trim().length < 3) {
                    activeField.style.borderColor = 'red';
                } else {
                    activeField.style.borderColor = '';
                }
            }
        }

        function getActiveDocumentField() {
            if (!docTypeSelect) return null;

            switch(docTypeSelect.value) {
                case 'id': return idInput;
                case 'passport': return passportInput;
                case 'driver_license': return driverLicenseInput;
                case 'other': return otherDocInput;
                default: return idInput;
            }
        }

        // Set up validation for all document fields
        [idInput, passportInput, driverLicenseInput, otherDocInput].forEach(input => {
            if (!input) return;

            input.addEventListener('focus', validateCurrentField);
            input.addEventListener('input', validateCurrentField);
            input.addEventListener('blur', validateCurrentField);
        });
    }

    // Initialize document validation
    setupDocumentValidation();

    // Form submission validation (updated to check all document types)
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const docTypeSelect = form.querySelector('select[name="id_document_type"]');
            const activeField = docTypeSelect ?
                form.querySelector(`input[name="${getFieldNameForDocType(docTypeSelect.value)}"]`) :
                null;

            if (activeField && activeField.value.trim().length > 0) {
                if (activeField.name === 'id_number') {
                    const result = validateSAIdNumber(activeField.value);
                    if (!result.valid) {
                        e.preventDefault();
                        alert('Please enter a valid South African ID number before submitting.');
                        activeField.focus();
                    }
                } else if (activeField.value.trim().length < 3) {
                    e.preventDefault();
                    alert('Please enter a valid document number before submitting.');
                    activeField.focus();
                }
            }
        });
    });

    function getFieldNameForDocType(docType) {
        switch(docType) {
            case 'id': return 'id_number';
            case 'passport': return 'passport_number';
            case 'driver_license': return 'driver_license_number';
            case 'other': return 'id_number_other';
            default: return 'id_number';
        }
    }

    // Document type switching (updated to match your existing implementation)
    const docTypeSelect = document.querySelector('select[name="id_document_type"]');
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

        // Show appropriate field (using your existing type codes)
        if (docType === 'ID' || docType === 'BC') {
            if (idNumberField) idNumberField.style.display = 'block';
        } else if (docType === 'PP') {
            if (passportField) passportField.style.display = 'block';
        } else if (docType === 'DL') {
            if (driverLicenseField) driverLicenseField.style.display = 'block';
        } else if (docType === 'OT') {
            if (otherDocumentField) otherDocumentField.style.display = 'block';
        }
    }

    if (docTypeSelect) {
        docTypeSelect.addEventListener('change', updateFields);
        updateFields(); // Initialize on load
    }
});
