// Clean registration form JavaScript

$(document).ready(function() {
    console.log("SIMPLIFIED DEBUG: Working with actual elements");
    
    const docTypeField = $('#id_id_document_type');
    const idNumberContainer = $('#div_id_id_number');
    const dobField = $('#id_date_of_birth');
    const genderField = $('#id_gender');
    const roleField = $('#id_role');
    const nameField = $('#id_name');
    const surnameField = $('#id_surname');
    const popiCheckbox = $('#id_popi_act_consent');
    const submitBtn = $('#submit-btn');
    
    console.log("Found elements:", {
        docType: docTypeField.length,
        idContainer: idNumberContainer.length,
        dob: dobField.length,
        gender: genderField.length,
        role: roleField.length,
        popi: popiCheckbox.length,
        submit: submitBtn.length,
        name: nameField.length,
        surname: surnameField.length
    });
    
    // Add blank option to Role field
    if (roleField.length && roleField.find('option[value=""]').length === 0) {
        roleField.prepend('<option value="">---------</option>');
        roleField.val('');
        console.log("Added blank option to Role field");
    }
    
    // Document type change handling
    function handleDocTypeChange() {
        const selectedType = docTypeField.val();
        console.log("Document type changed to:", selectedType);
        
        // Get field references
        const idNumberField = $('#id_id_number');
        const passportNumberField = $('#id_passport_number');
        
        if (selectedType === 'ID' || selectedType === 'BC') {
            // Clear passport number when switching to ID
            if (passportNumberField) passportNumberField.val('');
            
            // Clear DOB and gender fields
            dobField.val('');
            genderField.val('');
            
            idNumberContainer.show();
            dobField.prop('disabled', true);
            genderField.prop('disabled', true);
            console.log("ID/BC selected - showing ID field");
        } else {
            // Clear ID number when switching to passport
            idNumberField.val('');
            
            // Clear and enable DOB and gender fields for manual entry
            dobField.val('');
            genderField.val('');
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            
            // Reset styling for manual entry
            dobField.css({
                'backgroundColor': '',
                'cursor': '',
                'title': ''
            });
            genderField.css({
                'backgroundColor': '',
                'cursor': '',
                'title': ''
            });
            
            idNumberContainer.hide();
            console.log("Non-ID/BC selected - hiding ID field, clearing ID number");
        }
        
        checkPopiConsentEligibility();
    }
    
    // Role change handling
    function handleRoleChange() {
        const selectedRole = roleField.val();
        console.log("Role changed to:", selectedRole);
        
        setTimeout(function() {
            if (selectedRole === 'ADMIN_PROVINCE') {
                $('.province-field-wrapper').show();
                console.log("PROVINCE ADMIN: Showing only province field");
            } else if (selectedRole === 'ADMIN_REGION') {
                $('.province-field-wrapper').show();
                $('.region-field-wrapper').show();
                $('.province-field-wrapper').css('display', 'block');
                $('.region-field-wrapper').css('display', 'block');
                console.log("REGION ADMIN: Both fields should now be visible");
            } else if (selectedRole === 'ADMIN_LOCAL_FED') {
                $('.province-field-wrapper, .region-field-wrapper, .lfa-field-wrapper').show();
            } else if (selectedRole === 'CLUB_ADMIN') {
                $('.province-field-wrapper, .region-field-wrapper, .lfa-field-wrapper, .club-field-wrapper').show();
            } else {
                $('.province-field-wrapper, .region-field-wrapper, .lfa-field-wrapper, .club-field-wrapper').hide();
            }
            updateSubmitButton();
        }, 100);
    }
    
    // POPI consent eligibility check
    function checkPopiConsentEligibility() {
        const docType = docTypeField.val();
        let shouldEnable = false;
        
        if (docType === 'ID' || docType === 'BC') {
            const idNumber = $('#id_id_number').val();
            if (idNumber && idNumber.length === 13) {
                shouldEnable = true;
            }
        } else if (docType === 'PP' || docType === 'DL' || docType === 'OT') {
            const dob = dobField.val();
            const gender = genderField.val();
            if (dob && gender) {
                shouldEnable = true;
            }
        }
        
        if (shouldEnable) {
            popiCheckbox.prop('disabled', false);
            $('#div_id_popi_act_consent').removeClass('text-muted');
            console.log("POPI consent ENABLED");
        } else {
            popiCheckbox.prop('disabled', true).prop('checked', false);
            $('#div_id_popi_act_consent').addClass('text-muted');
            console.log("POPI consent DISABLED");
        }
        
        updateSubmitButton();
    }
    
    // Submit button state management
    function updateSubmitButton() {
        const isPopiChecked = popiCheckbox.is(':checked');
        const roleSelected = roleField.val() !== '';
        const nameValid = nameField.val().length >= 3;
        const surnameValid = surnameField.val().length >= 3;
        const emailValid = $('#id_email').val().includes('@') && !$('#id_email').hasClass('is-invalid');
        const passwordValid = $('#id_password1').val().length >= 8;
        const passwordMatch = $('#id_password1').val() === $('#id_password2').val();
        const idNumberValid = !$('#id_id_number').hasClass('is-invalid');
        
        // Check admin fields based on role
        let adminFieldsValid = true;
        const selectedRole = roleField.val();
        
        if (selectedRole === 'ADMIN_PROVINCE') {
            adminFieldsValid = $('#id_province').val() !== '';
        } else if (selectedRole === 'ADMIN_REGION') {
            adminFieldsValid = $('#id_province').val() !== '' && $('#id_region').val() !== '';
        }
        
        const canSubmit = isPopiChecked && roleSelected && nameValid && surnameValid && emailValid && passwordValid && passwordMatch && adminFieldsValid && idNumberValid;
        
        submitBtn.prop('disabled', !canSubmit);
        
        if (canSubmit) {
            submitBtn.removeClass('btn-secondary').addClass('btn-dark');
        } else {
            submitBtn.removeClass('btn-dark').addClass('btn-secondary');
        }
    }
    
    // Password validation
    $('#id_password1').on('focus', function() {
        $('#password-validation').slideDown(200);
    });
    
    $('#id_password1').on('blur', function() {
        const password = $(this).val();
        if (password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /\d/.test(password) && /[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            $('#password-validation').slideUp(200);
        }
    });
    
    $('#id_password1').on('input', function() {
        const password = $(this).val();
        
        // Check length
        if (password.length >= 8) {
            $('#length-validation').removeClass('invalid').addClass('valid').find('i').removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            $('#length-validation').removeClass('valid').addClass('invalid').find('i').removeClass('fa-check-circle').addClass('fa-times-circle');
        }
        
        // Check uppercase
        if (/[A-Z]/.test(password)) {
            $('#uppercase-validation').removeClass('invalid').addClass('valid').find('i').removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            $('#uppercase-validation').removeClass('valid').addClass('invalid').find('i').removeClass('fa-check-circle').addClass('fa-times-circle');
        }
        
        // Check lowercase
        if (/[a-z]/.test(password)) {
            $('#lowercase-validation').removeClass('invalid').addClass('valid').find('i').removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            $('#lowercase-validation').removeClass('valid').addClass('invalid').find('i').removeClass('fa-check-circle').addClass('fa-times-circle');
        }
        
        // Check number
        if (/\d/.test(password)) {
            $('#number-validation').removeClass('invalid').addClass('valid').find('i').removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            $('#number-validation').removeClass('valid').addClass('invalid').find('i').removeClass('fa-check-circle').addClass('fa-times-circle');
        }
        
        // Check special character
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            $('#special-validation').removeClass('invalid').addClass('valid').find('i').removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            $('#special-validation').removeClass('valid').addClass('invalid').find('i').removeClass('fa-check-circle').addClass('fa-times-circle');
        }
        
        updateSubmitButton();
    });
    
    // ID number validation and auto-population
    $('#id_id_number').on('input', function() {
        const idValue = $(this).val().replace(/\D/g, '');
        console.log("ID number changed:", idValue, "Length:", idValue.length);
        
        if (idValue.length === 13) {
            // Extract date of birth (YYMMDD)
            const year = parseInt(idValue.substring(0, 2));
            const month = parseInt(idValue.substring(2, 4));
            const day = parseInt(idValue.substring(4, 6));
            
            // Determine century
            const fullYear = year <= 25 ? 2000 + year : 1900 + year;
            
            // Extract gender (7th digit: 0-4 = female, 5-9 = male)
            const genderDigit = parseInt(idValue.substring(6, 7));
            const gender = genderDigit >= 5 ? 'M' : 'F';
            
            // Format date for input field
            const formattedDate = `${fullYear}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            
            // Populate fields
            dobField.val(formattedDate);
            genderField.val(gender);
            
            console.log("Auto-populated from ID:", {
                dob: formattedDate,
                gender: gender,
                genderDigit: genderDigit
            });
        } else {
            dobField.val('');
            genderField.val('');
        }
        
        checkPopiConsentEligibility();
    });
    
    // Email uniqueness validation
    let emailCheckTimeout;
    $('#id_email').on('input', function() {
        const email = $(this).val();
        clearTimeout(emailCheckTimeout);
        $('.email-error').remove();
        
        if (email.includes('@')) {
            emailCheckTimeout = setTimeout(function() {
                $.ajax({
                    url: '/accounts/ajax/check-email/',
                    data: { email: email },
                    success: function(response) {
                        if (response.exists) {
                            $('#id_email').addClass('is-invalid');
                            $('#id_email').after('<div class="email-error text-danger">This email is already registered.</div>');
                        } else {
                            $('#id_email').removeClass('is-invalid').addClass('is-valid');
                        }
                        updateSubmitButton();
                    }
                });
            }, 500);
        }
    });
    
    // ID number uniqueness validation - ENHANCED
    let idCheckTimeout;
    $('#id_id_number').on('input', function() {
        const idValue = $(this).val().replace(/\D/g, '');
        clearTimeout(idCheckTimeout);
        $('.id-error').remove();
        
        // Only check uniqueness if ID number is not empty
        if (idValue.length === 13) {
            idCheckTimeout = setTimeout(function() {
                $.ajax({
                    url: '/accounts/ajax/check-id-number/',
                    data: { id_number: idValue },
                    success: function(response) {
                        if (response.exists) {
                            $('#id_id_number').addClass('is-invalid');
                            $('#id_id_number').after('<div class="id-error text-danger">This ID number is already registered.</div>');
                        } else {
                            $('#id_id_number').removeClass('is-invalid').addClass('is-valid');
                        }
                        updateSubmitButton();
                    },
                    error: function() {
                        console.log("ID uniqueness check endpoint not implemented yet");
                    }
                });
            }, 500);
        } else if (idValue.length > 0 && idValue.length < 13) {
            // Show validation error for incomplete ID numbers
            $('#id_id_number').addClass('is-invalid');
            $('#id_id_number').after('<div class="id-error text-danger">ID number must be exactly 13 digits.</div>');
            updateSubmitButton();
        } else {
            // Empty ID number is valid for passport users
            $('#id_id_number').removeClass('is-invalid is-valid');
            updateSubmitButton();
        }
    });
    
    // Province change - populate regions with REAL data
    $('#id_province').on('change', function() {
        const provinceId = $(this).val();
        const regionSelect = $('#id_region');
        
        regionSelect.html('<option value="">---------</option>');
        
        if (provinceId) {
            // Make AJAX call to get real regions
            $.ajax({
                url: '/geography/api/regions-by-province/' + provinceId + '/',
                method: 'GET',
                success: function(response) {
                    if (response.regions && response.regions.length > 0) {
                        response.regions.forEach(function(region) {
                            regionSelect.append(`<option value="${region.id}">${region.name}</option>`);
                        });
                        console.log("Added real regions for province:", provinceId);
                    } else {
                        console.log("No regions found for province:", provinceId);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Failed to load regions:", error);
                    // Fallback to test data if API fails
                    const fallbackRegions = [
                        {id: 1, name: 'Region A (Fallback)'},
                        {id: 2, name: 'Region B (Fallback)'}
                    ];
                    fallbackRegions.forEach(function(region) {
                        regionSelect.append(`<option value="${region.id}">${region.name}</option>`);
                    });
                }
            });
        }
    });
    
    // Event bindings
    docTypeField.on('change', handleDocTypeChange);
    roleField.on('change', handleRoleChange);
    dobField.on('change', checkPopiConsentEligibility);
    genderField.on('change', checkPopiConsentEligibility);
    popiCheckbox.on('change', updateSubmitButton);
    nameField.on('input', updateSubmitButton);
    surnameField.on('input', updateSubmitButton);
    $('#id_password2').on('input', updateSubmitButton);
    $('#id_province').on('change', updateSubmitButton);
    $('#id_region').on('change', updateSubmitButton);
    
    // Initial setup
    handleDocTypeChange();
    checkPopiConsentEligibility();
    updateSubmitButton();
    
    // Hide password validation on page load
    $('#password-validation').hide();
    
    // Hide any Django/crispy forms password help text
    $('#div_id_password1 .form-text').hide();
    $('#div_id_password2 .form-text').hide();
    $('.password-help-text').hide();
    
    console.log("Registration debug script loaded successfully");
});
