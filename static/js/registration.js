$(document).ready(function() {
    const form = $('#registration-form');
    const idNumberField = $('#' + form.data('id-number-id'));
    const countryField = $('#' + form.data('country-id'));
    const dobField = $('#' + form.data('dob-id'));
    const genderField = $('#' + form.data('gender-id'));
    const idDocTypeField = $('#' + form.data('id-doc-type-id'));

    const idNumberBox = $('#id_number_box');
    const passportBox = $('#passport_box');
    const documentBox = $('#document_box');
    const documentField = $('#id_id_document');  // Changed from id_document

    function validateSouthAfricanID(idNumber) {
        idNumber = idNumber.replace(/\s+/g, '').replace(/-/g, '');
        if (!/^\d{13}$/.test(idNumber)) {
            return false;
        }
        const year = idNumber.substring(0, 2);
        const month = idNumber.substring(2, 4);
        const day = idNumber.substring(4, 6);
        const currentYear = new Date().getFullYear() % 100;
        const century = (parseInt(year) > currentYear) ? '19' : '20';
        const fullYear = century + year;
        const date = new Date(fullYear, parseInt(month) - 1, parseInt(day));
        if (date.getFullYear() != parseInt(fullYear) ||
            date.getMonth() != parseInt(month) - 1 ||
            date.getDate() != parseInt(day)) {
            return false;
        }
        const genderDigits = parseInt(idNumber.substring(6, 10));
        const gender = genderDigits >= 5000 ? 'M' : 'F';
        const citizenship = parseInt(idNumber.charAt(10));
        if (citizenship !== 0 && citizenship !== 1) {
            return false;
        }
        let total = 0;
        for (let i = 0; i < 12; i++) {
            let digit = parseInt(idNumber.charAt(i));
            if (i % 2 === 0) {
                total += digit;
            } else {
                let doubled = digit * 2;
                total += doubled < 10 ? doubled : (doubled - 9);
            }
        }
        const checkDigit = (10 - (total % 10)) % 10;
        if (checkDigit !== parseInt(idNumber.charAt(12))) {
            return false;
        }
        return {
            dateOfBirth: date,
            gender: gender
        };
    }

    function handleDocumentTypeChange() {
        const selectedDocType = idDocTypeField.val();
        if (selectedDocType === 'ID' || selectedDocType === 'BC') {
            idNumberBox.show();
            passportBox.hide();
            documentBox.show();
        } else if (selectedDocType === 'PP') {
            idNumberBox.hide();
            passportBox.show();
            documentBox.show();
        } else {
            idNumberBox.hide();
            passportBox.hide();
            documentBox.show();
        }
        // Enable country field for passport, disable for others (handled in handleIDNumberChange for valid ID/BC)
        if (selectedDocType === 'PP') {
            countryField.prop('disabled', false);
        }
    }

    function showSouthAfricaFlag(show) {
        if (show) {
            $('#country-flag').show();
            $('#country-code').text('ZAF');
        } else {
            $('#country-flag').hide();
            $('#country-code').text('');
        }
    }

    function setCountryToSouthAfrica() {
        countryField.find('option').each(function() {
            if ($(this).text().toLowerCase().includes('south africa')) {
                countryField.val($(this).val()).trigger('change');
            }
        });
        showSouthAfricaFlag(true);
    }

    function handleIDNumberChange() {
        let idNumber = idNumberField.val();
        const selectedDocType = idDocTypeField.val();
        const errorDiv = $('#id_number_error');
        const extraFields = $('#id-extra-fields');
        errorDiv.hide().text('');
        extraFields.hide();

        if (selectedDocType !== 'ID' && selectedDocType !== 'BC') {
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            return;
        }

        idNumberField.attr('maxlength', '13');
        if (idNumber.length > 13) {
            idNumber = idNumber.substring(0, 13);
            idNumberField.val(idNumber);
        }

        if (idNumber && idNumber.length === 13) {
            const validationResult = validateSouthAfricanID(idNumber);
            if (validationResult) {
                const date = validationResult.dateOfBirth;
                const yyyy = date.getFullYear();
                const mm = String(date.getMonth() + 1).padStart(2, '0');
                const dd = String(date.getDate()).padStart(2, '0');
                const formattedDate = yyyy + '-' + mm + '-' + dd;
                dobField.val(formattedDate);
                dobField.prop('disabled', true);
                genderField.val(validationResult.gender);
                genderField.prop('disabled', true);

                // Set and lock country to South Africa, show flag/code
                setCountryToSouthAfrica();
                countryField.prop('disabled', true).addClass('readonly-country');
                showSouthAfricaFlag(true);
                extraFields.show();
            } else {
                errorDiv.text('Invalid South African ID/Birth Certificate number.').show();
            }
        } else if (idNumber.length > 0 && idNumber.length < 13) {
            errorDiv.text('Number must be exactly 13 digits.').show();
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            countryField.prop('disabled', false).removeClass('readonly-country');
            showSouthAfricaFlag(false);
        } else {
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            countryField.prop('disabled', false).removeClass('readonly-country');
            showSouthAfricaFlag(false);
        }
    }

    // Email AJAX check
    const emailField = $('#id_email');
    if ($('#email-exists-error').length === 0) {
        emailField.after('<div class="text-danger" id="email-exists-error" style="display:none;"></div>');
    }
    const emailErrorDiv = $('#email-exists-error');

    // Change 'blur' to 'input' for real-time checking
    emailField.on('input', function() {
        const email = emailField.val().trim();
        if (email.length > 0) {
            $.get('/accounts/ajax/check-email/', {email: email}, function(data) {
                if (data.exists) {
                    emailErrorDiv.text('This email is already registered.').show();
                } else {
                    emailErrorDiv.hide();
                }
            });
        } else {
            emailErrorDiv.hide();
        }
    });

    idNumberField.on('input', handleIDNumberChange);
    idDocTypeField.on('change', function() {
        handleDocumentTypeChange();
        handleIDNumberChange();
    });

    handleDocumentTypeChange();
    handleIDNumberChange();

    // Show/hide province field based on role
    $('#id_role').change(function() {
        if ($(this).val() === 'ADMIN_PROVINCE') {
            $('.province-field-wrapper').show();
        } else {
            $('.province-field-wrapper').hide();
        }
    }).trigger('change'); // Trigger on page load

    // Add this to your registration.js file:
    $(document).ready(function() {
        // Add this debugging code
        console.log("Province field found:", $('.province-field-wrapper').length);
        console.log("Role field value:", $('#id_role').val());
        
        // Make province field obvious on page load
        $('.province-field-wrapper').addClass('bg-light');
        
        // Your existing role change handler
        $('#id_role').change(function() {
            console.log("Role changed to:", $(this).val());
            if ($(this).val() === 'ADMIN_PROVINCE') {
                console.log("Should show province field");
                $('.province-field-wrapper').show().css('display', 'block !important');
            } else {
                console.log("Should hide province field");
                $('.province-field-wrapper').hide();
            }
        }).trigger('change');
    });

    // Hide all admin fields initially
    $('.admin-field-wrapper').hide();
    
    // Show appropriate field based on role selection
    $('#id_role').change(function() {
        // Hide all admin fields first
        $('.admin-field-wrapper').hide();
        
        // Show the specific field for the selected role
        const role = $(this).val();
        
        if (role === 'ADMIN_PROVINCE') {
            $('.province-field-wrapper').show();
        } else if (role === 'ADMIN_REGION') {
            $('.region-field-wrapper').show();
        } else if (role === 'ADMIN_LOCAL_FED') {
            $('.lfa-field-wrapper').show();
        } else if (role === 'CLUB_ADMIN') {
            $('.club-field-wrapper').show();
        }
    }).trigger('change');  // Trigger on page load

    $('#registration-form').on('submit', function(e) {
        // Check for any visible errors
        if ($('.text-danger:visible').length > 0) {
            e.preventDefault();
            alert('Please fix the errors before submitting.');
        }
        
        // Verify required fields
        const requiredFields = ['email', 'password1', 'password2', 'name', 'surname', 'role'];
        let missingFields = [];
        
        requiredFields.forEach(function(field) {
            if ($('#id_' + field).val() === '') {
                missingFields.push(field);
                $('#id_' + field).addClass('is-invalid');
            } else {
                $('#id_' + field).removeClass('is-invalid');
            }
        });
        
        if (missingFields.length > 0) {
            e.preventDefault();
            alert('Please fill in all required fields: ' + missingFields.join(', '));
        }
    });
});