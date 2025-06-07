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
        
        // First hide/show appropriate sections
        if (selectedDocType === 'ID' || selectedDocType === 'BC') {
            idNumberBox.show();
            passportBox.hide();
            documentBox.show();
            
            // Always disable DOB and gender fields for ID/Birth Certificate
            dobField.prop('disabled', true);
            genderField.prop('disabled', true);
            
        } else if (selectedDocType === 'PP') {
            idNumberBox.hide();
            passportBox.show();
            documentBox.show();
            
            // Enable fields for passport
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            
        } else {
            // For other document types (DL, OT)
            idNumberBox.hide();
            passportBox.hide();
            documentBox.show();
            
            // Enable fields for other document types
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
        }
        
        // Enable country field for passport, disable for others
        if (selectedDocType === 'PP') {
            countryField.prop('disabled', false);
        } else if (selectedDocType === 'ID' || selectedDocType === 'BC') {
            // For SA IDs, lock to South Africa
            setCountryToSouthAfrica();
            countryField.prop('disabled', true);
        } else {
            // For other types, enable country selection
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

        // Always disable DOB and gender fields for ID/BC document types
        // regardless of ID number content
        if (selectedDocType === 'ID' || selectedDocType === 'BC') {
            dobField.prop('disabled', true);
            genderField.prop('disabled', true);
        }

        // If not ID or Birth Certificate, skip validation
        if (selectedDocType !== 'ID' && selectedDocType !== 'BC') {
            return;
        }

        idNumberField.attr('maxlength', '13');
        if (idNumber.length > 13) {
            idNumber = idNumber.substring(0, 13);
            idNumberField.val(idNumber);
        }

        // Clear fields if ID number is deleted
        if (!idNumber || idNumber.length === 0) {
            dobField.val('');
            genderField.val('');
            return;
        }

        if (idNumber.length === 13) {
            const validationResult = validateSouthAfricanID(idNumber);
            if (validationResult) {
                const date = validationResult.dateOfBirth;
                const yyyy = date.getFullYear();
                const mm = String(date.getMonth() + 1).padStart(2, '0');
                const dd = String(date.getDate()).padStart(2, '0');
                const formattedDate = yyyy + '-' + mm + '-' + dd;
                
                // Set values but keep fields disabled
                dobField.val(formattedDate);
                genderField.val(validationResult.gender);
                
                // Always keep fields disabled for ID/BC
                dobField.prop('disabled', true);
                genderField.prop('disabled', true);

                // Set and lock country to South Africa
                setCountryToSouthAfrica();
                countryField.prop('disabled', true).addClass('readonly-country');
                
                // Hide any existing error
                errorDiv.hide();
            } else {
                // Show error for invalid ID
                errorDiv.text('Invalid South African ID/Birth Certificate number.').show();
                
                // Clear fields on invalid ID
                dobField.val('');
                genderField.val('');
            }
        } else if (idNumber.length > 0) {
            // Show error for incomplete ID
            errorDiv.text('ID number must be exactly 13 digits.').show();
            
            // Clear fields when ID is incomplete
            dobField.val('');
            genderField.val('');
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

    // Show/hide province field based on role - only keep province handling
    $('#id_role').change(function() {
        if ($(this).val() === 'ADMIN_PROVINCE') {
            $('.province-field-wrapper').show();
        } else {
            $('.province-field-wrapper').hide();
        }
    }).trigger('change'); // Trigger on page load

    // Remove nested document.ready that causes duplicate handlers
    console.log("Province field found:", $('.province-field-wrapper').length);
    console.log("Role field value:", $('#id_role').val());
    
    // Make province field obvious on page load
    $('.province-field-wrapper').addClass('bg-light');
    
    // Remove the redundant admin field handlers for fields that don't exist
    // Keep only province handling
    $('#id_role').change(function() {
        if ($(this).val() === 'ADMIN_PROVINCE') {
            $('.province-field-wrapper').show();
        } else {
            $('.province-field-wrapper').hide();
        }
    }).trigger('change');

    // Form submission validation
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

    // Password validation code
    const passwordField = $('#id_password1');
    const confirmPasswordField = $('#id_password2');
    const validationDiv = $('#password-validation');
    
    // Hide Django's default help text
    passwordField.siblings('.form-text').hide().addClass('password-help-text');
    
    // Fix password confirmation field styling
    $('#div_id_password2').css('margin-top', '1rem');
    
    // Show validation on focus
    passwordField.on('focus', function() {
      validationDiv.show();
    });
    
    // Hide validation when focus moves to another field 
    // (only if we're not focusing on confirm password)
    passwordField.on('blur', function() {
      if (!confirmPasswordField.is(':focus')) {
        validationDiv.hide();
      }
    });
    
    // Keep validation visible when focusing on confirm password
    confirmPasswordField.on('focus', function() {
      validationDiv.show();
    });
    
    // Hide validation when leaving confirm password
    // (only if we're not focusing on password field)
    confirmPasswordField.on('blur', function() {
      if (!passwordField.is(':focus')) {
        validationDiv.hide();
      }
    });
    
    // Check password requirements in real-time
    passwordField.on('keyup', function() {
      validatePassword($(this).val());
    });
    
    // Validate password again if pasted
    passwordField.on('paste', function() {
      setTimeout(function() {
        validatePassword(passwordField.val());
      }, 100);
    });
    
    function validatePassword(password) {
      // Check length
      if (password.length >= 8) {
        $('#length-validation').removeClass('invalid').addClass('valid');
        $('#length-validation i').removeClass('fa-times-circle').addClass('fa-check-circle');
      } else {
        $('#length-validation').removeClass('valid').addClass('invalid');
        $('#length-validation i').removeClass('fa-check-circle').addClass('fa-times-circle');
      }
      
      // Check uppercase
      if (/[A-Z]/.test(password)) {
        $('#uppercase-validation').removeClass('invalid').addClass('valid');
        $('#uppercase-validation i').removeClass('fa-times-circle').addClass('fa-check-circle');
      } else {
        $('#uppercase-validation').removeClass('valid').addClass('invalid');
        $('#uppercase-validation i').removeClass('fa-check-circle').addClass('fa-times-circle');
      }
      
      // Check lowercase
      if (/[a-z]/.test(password)) {
        $('#lowercase-validation').removeClass('invalid').addClass('valid');
        $('#lowercase-validation i').removeClass('fa-times-circle').addClass('fa-check-circle');
      } else {
        $('#lowercase-validation').removeClass('valid').addClass('invalid');
        $('#lowercase-validation i').removeClass('fa-check-circle').addClass('fa-times-circle');
      }
      
      // Check numbers
      if (/[0-9]/.test(password)) {
        $('#number-validation').removeClass('invalid').addClass('valid');
        $('#number-validation i').removeClass('fa-times-circle').addClass('fa-check-circle');
      } else {
        $('#number-validation').removeClass('valid').addClass('invalid');
        $('#number-validation i').removeClass('fa-check-circle').addClass('fa-times-circle');
      }
      
      // Check special character
      if (/[^A-Za-z0-9]/.test(password)) {
        $('#special-validation').removeClass('invalid').addClass('valid');
        $('#special-validation i').removeClass('fa-times-circle').addClass('fa-check-circle');
      } else {
        $('#special-validation').removeClass('valid').addClass('invalid');
        $('#special-validation i').removeClass('fa-check-circle').addClass('fa-times-circle');
      }
    }
    
    // Check password match
    confirmPasswordField.on('keyup', function() {
      const password = passwordField.val();
      const confirmPassword = $(this).val();
      
      if (password && confirmPassword) {
        if (password === confirmPassword) {
          confirmPasswordField.removeClass('is-invalid').addClass('is-valid');
          $('#password-match-error').hide();
        } else {
          confirmPasswordField.removeClass('is-valid').addClass('is-invalid');
          if ($('#password-match-error').length === 0) {
            confirmPasswordField.after('<div id="password-match-error" class="text-danger">Passwords do not match</div>');
          } else {
            $('#password-match-error').show();
          }
        }
      } else {
        confirmPasswordField.removeClass('is-valid is-invalid');
        $('#password-match-error').hide();
      }
    });
    
    // Add additional initialization at the end of document ready
    $(function() {
        // Ensure DOB and gender fields are disabled by default
        dobField.prop('disabled', true);
        genderField.prop('disabled', true);
        
        // Add a prominent indicator to disabled fields
        $('input:disabled, select:disabled').addClass('field-disabled');
        
        // Add CSS for disabled fields
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .field-disabled {
                    background-color: #f8f9fa !important;
                    cursor: not-allowed;
                    opacity: 0.8;
                }
            `)
            .appendTo('head');
            
        // Trigger handlers to set initial state
        handleDocumentTypeChange();
        handleIDNumberChange();
    });
});