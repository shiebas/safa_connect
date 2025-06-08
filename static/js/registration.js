$(document).ready(function() {
    // Direct element references - ensure we use consistent prefixes
    const idNumberField = $('#id_id_number');
    const idNumberOtherField = $('#id_id_number_other');
    const passportNumberField = $('#id_passport_number');
    const countryField = $('#id_country');
    const dobField = $('#id_date_of_birth');
    const genderField = $('#id_gender');
    const idDocTypeField = $('#id_id_document_type');
    
    // Direct references to parent containers
    const idNumberBox = $('#id_number_box');
    const idNumberOtherBox = $('#id_number_other_box');
    const passportBox = $('#passport_box');
    const documentBox = $('#document_box');
    const documentField = $('#id_id_document');
    
    // Debug log - remove when working
    console.log("Registration JS loaded. Elements found:", {
        idDocTypeField: idDocTypeField.length,
        idNumberBox: idNumberBox.length,
        passportBox: passportBox.length,
        idNumberOtherBox: idNumberOtherBox.length
    });
    

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

    // SIMPLIFIED document type handler - remove all complexity
    function handleDocumentTypeChange() {
        const selectedDocType = idDocTypeField.val();
        console.log("Document type changed to:", selectedDocType);
        
        // Hide ALL boxes first
        idNumberBox.hide();
        passportBox.hide();
        idNumberOtherBox.hide();
        
        // Show appropriate box based on selection
        switch(selectedDocType) {
            case 'ID':
                idNumberBox.show();
                dobField.prop('disabled', true);
                genderField.prop('disabled', true);
                break;
            case 'PASSPORT':
                passportBox.show();
                dobField.prop('disabled', false);
                genderField.prop('disabled', false);
                break;
            case 'OTHER':
                idNumberOtherBox.show();
                dobField.prop('disabled', false);
                genderField.prop('disabled', false);
                break;
            default:
                // No selection - hide all
                break;
        }
        
        console.log("Visibility after change:", {
            idBox: idNumberBox.is(':visible'),
            passportBox: passportBox.is(':visible'),
            otherBox: idNumberOtherBox.is(':visible')
        });
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

    // Add CSRF token to all AJAX requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Set up CSRF token for all AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

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

    // CLEAN event binding - remove all duplicate handlers
    idDocTypeField.off('change.doctype');
    idDocTypeField.on('change.doctype', handleDocumentTypeChange);
    
    // Initial setup
    handleDocumentTypeChange();

    idNumberField.on('input', handleIDNumberChange);
    idDocTypeField.on('change', function() {
        console.log("Document type change triggered");
        handleDocumentTypeChange();
        handleIDNumberChange();
    });

    // Move event bindings to a more prominent location
    $(function() {
        // Make sure our event handlers are registered
        idNumberField.on('input', handleIDNumberChange);
        
        idDocTypeField.on('change', function() {
            console.log("Document type change triggered");
            handleDocumentTypeChange();
            handleIDNumberChange();
        });
        
        // Force initial setup
        console.log("Initial setup - document type:", idDocTypeField.val());
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

        // Show/hide admin fields based on role selection
        $('#id_role').change(function() {
            // Hide all admin fields first
            $('.admin-field-wrapper').hide();
            
            // Show relevant fields based on selected role
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
        }).trigger('change'); // Trigger on page load
        
        // Add dependent dropdowns for geographical hierarchy
        $('#id_province').change(function() {
            const provinceId = $(this).val();
            if (provinceId) {
                // If a province is selected, filter the regions dropdown
                $.getJSON(`/geography/api/regions-by-province/${provinceId}/`, function(regions) {
                    const $regionSelect = $('#id_region');
                    $regionSelect.empty().append('<option value="">---------</option>');
                    
                    regions.forEach(function(region) {
                        $regionSelect.append(`<option value="${region.id}">${region.name}</option>`);
                    });
                });
            }
        });
        
        $('#id_region').change(function() {
            const regionId = $(this).val();
            if (regionId) {
                // If a region is selected, filter the LFAs dropdown
                $.getJSON(`/geography/api/lfas-by-region/${regionId}/`, function(lfas) {
                    const $lfaSelect = $('#id_local_federation');
                    $lfaSelect.empty().append('<option value="">---------</option>');
                    
                    lfas.forEach(function(lfa) {
                        $lfaSelect.append(`<option value="${lfa.id}">${lfa.name}</option>`);
                    });
                });
            }
        });
        
        // Form submission validation
        $('#registration-form').on('submit', function(e) {
            // Check for POPI Act consent
            const popiConsent = $('#id_popi_act_consent');
            if (popiConsent.length && !popiConsent.is(':checked')) {
                e.preventDefault();
                alert('You must agree to the POPI Act terms to register.');
                return false;
            }
            
            // Check for any visible errors
            if ($('.text-danger:visible').length > 0) {
                e.preventDefault();
                alert('Please fix the errors before submitting.');
                return false;
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
                return false;
            }
            
            // Make sure the CSRF token is included
            if (!$('input[name="csrfmiddlewaretoken"]').length) {
                // If there's no CSRF token field, add it
                const csrftoken = getCookie('csrftoken');
                $(this).append('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrftoken + '">');
            }
            
            // Form is valid, allow submission
            return true;
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
});