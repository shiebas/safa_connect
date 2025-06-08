// Simplified JavaScript to debug document type selection issue

$(document).ready(function() {
    console.log("SIMPLIFIED DEBUG: Working with actual elements");
    
    const docTypeField = $('#id_id_document_type');
    const idNumberContainer = $('#div_id_id_number');
    const dobField = $('#id_date_of_birth');
    const genderField = $('#id_gender');
    
    console.log("Found elements:", {
        docType: docTypeField.length,
        idContainer: idNumberContainer.length,
        dob: dobField.length,
        gender: genderField.length
    });
    
    function handleDocTypeChange() {
        const selectedType = docTypeField.val();
        console.log("Document type changed to:", selectedType);
        
        // Always clear ALL fields when switching document types
        const idNumberField = $('#id_id_number');
        dobField.val('');
        genderField.val('');
        idNumberField.val(''); // Clear ID number too
        console.log("Cleared DOB, gender, and ID number fields");
        
        // Birth Certificate and National ID both contain ID numbers
        if (selectedType === 'ID' || selectedType === 'BC') {
            // Show ID number field and disable DOB/gender (auto-populated from ID)
            idNumberContainer.show();
            dobField.prop('disabled', true);
            genderField.prop('disabled', true);
            console.log("ID/BC selected - showing ID field, disabling DOB/gender");
        } else {
            // For passport/other, hide ID number field and enable DOB/gender for manual entry
            idNumberContainer.hide();
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            console.log("Non-ID/BC selected - hiding ID field, enabling DOB/gender");
        }
        
        console.log("Final state:", {
            idContainerVisible: idNumberContainer.is(':visible'),
            dobDisabled: dobField.prop('disabled'),
            genderDisabled: genderField.prop('disabled'),
            dobValue: dobField.val(),
            genderValue: genderField.val(),
            idNumberValue: idNumberField.val()
        });
    }
    
    // Bind event and test
    docTypeField.on('change', handleDocTypeChange);
    handleDocTypeChange(); // Initial setup
    
    // Add name validation
    const nameField = $('#id_name');
    const surnameField = $('#id_surname');
    
    function validateName(field, fieldName) {
        const value = field.val();
        const alphabeticRegex = /^[A-Za-z\s]+$/;
        let errorDiv = field.next('.name-error');
        
        // Create error div if it doesn't exist
        if (errorDiv.length === 0) {
            field.after('<div class="name-error text-danger" style="display:none;"></div>');
            errorDiv = field.next('.name-error');
        }
        
        if (value.length > 0) {
            if (value.length < 3) {
                errorDiv.text(`${fieldName} must be at least 3 characters long.`).show();
                field.addClass('is-invalid');
            } else if (!alphabeticRegex.test(value)) {
                errorDiv.text(`${fieldName} can only contain alphabetic letters and spaces.`).show();
                field.addClass('is-invalid');
            } else {
                errorDiv.hide();
                field.removeClass('is-invalid').addClass('is-valid');
            }
        } else {
            errorDiv.hide();
            field.removeClass('is-invalid is-valid');
        }
    }
    
    // Bind name validation events
    nameField.on('input', function() {
        validateName($(this), 'First name');
    });
    
    surnameField.on('input', function() {
        validateName($(this), 'Surname');
    });
    
    // Add blank option to Role field to prevent auto-selection
    const roleField = $('#id_role');
    if (roleField.length && roleField.find('option[value=""]').length === 0) {
        roleField.prepend('<option value="">---------</option>');
        roleField.val(''); // Set to blank by default
        console.log("Added blank option to Role field");
    }
    
    // Add age validation (18+ required for administrators)
    dobField.on('change', function() {
        validateAge();
    });
    
    function validateAge() {
        const dobValue = dobField.val();
        if (!dobValue) return;
        
        const birthDate = new Date(dobValue);
        const today = new Date();
        const age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        
        // Adjust age if birthday hasn't occurred this year
        const actualAge = (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) 
            ? age - 1 : age;
        
        let ageErrorDiv = dobField.next('.age-error');
        if (ageErrorDiv.length === 0) {
            dobField.after('<div class="age-error text-danger" style="display:none;"></div>');
            ageErrorDiv = dobField.next('.age-error');
        }
        
        if (actualAge < 18) {
            ageErrorDiv.text('You must be at least 18 years old to register as an administrator.').show();
            dobField.addClass('is-invalid');
            console.log(`Age validation failed: ${actualAge} years old`);
        } else {
            ageErrorDiv.hide();
            dobField.removeClass('is-invalid').addClass('is-valid');
            console.log(`Age validation passed: ${actualAge} years old`);
        }
    }
    
    // Check if POPI Act consent checkbox exists
    const popiCheckbox = $('#id_popi_act_consent');
    console.log("POPI Act consent checkbox found:", popiCheckbox.length > 0 ? "YES" : "NO");
    
    if (popiCheckbox.length === 0) {
        console.warn("POPI Act consent checkbox not found in form!");
    } else {
        console.log("POPI Act consent checkbox is available and working");
        
        // Add visual feedback for POPI consent
        popiCheckbox.on('change', function() {
            if ($(this).is(':checked')) {
                $(this).removeClass('is-invalid').addClass('is-valid');
                console.log("POPI consent given");
            } else {
                $(this).removeClass('is-valid');
                console.log("POPI consent removed");
            }
        });
    }
});
