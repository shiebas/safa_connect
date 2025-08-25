
document.addEventListener('DOMContentLoaded', function() {
    const organizationType = document.getElementById('id_organization_type');
    const provinceField = document.getElementById('province-field');
    const regionField = document.getElementById('region-field');
    const lfaField = document.getElementById('lfa-field');
    const clubField = document.getElementById('club-field');

    const idDocumentType = document.getElementById('id_id_document_type');
    const saIdContainer = document.getElementById('sa-id-container');
    const passportContainer = document.getElementById('passport-container');
    const dobGenderManualRow = document.getElementById('dob-gender-manual-row');

    function toggleFields() {
        const selectedOrgTypeId = organizationType.value;

        if (selectedOrgTypeId) {
            // Fetch the organization type name from the server
            fetch(`/api/organization-type-name/${selectedOrgTypeId}/`)
                .then(response => response.json())
                .then(data => {
                    const orgTypeName = data.name.toUpperCase();

                    provinceField.style.display = 'none';
                    regionField.style.display = 'none';
                    lfaField.style.display = 'none';
                    clubField.style.display = 'none';

                    if (orgTypeName.includes('NATIONAL')) {
                        // All geo fields remain hidden
                    } else if (orgTypeName.includes('PROVINCE')) {
                        provinceField.style.display = 'block';
                    } else if (orgTypeName.includes('REGION')) {
                        provinceField.style.display = 'block';
                        regionField.style.display = 'block';
                    } else if (orgTypeName.includes('LFA') || orgTypeName.includes('LOCAL')) {
                        provinceField.style.display = 'block';
                        regionField.style.display = 'block';
                        lfaField.style.display = 'block';
                    } else if (orgTypeName.includes('CLUB')) {
                        provinceField.style.display = 'block';
                        regionField.style.display = 'block';
                        lfaField.style.display = 'block';
                        clubField.style.display = 'block';
                    }
                });
        } else {
            provinceField.style.display = 'none';
            regionField.style.display = 'none';
            lfaField.style.display = 'none';
            clubField.style.display = 'none';
        }
    }

    function updateRegions() {
        const provinceId = document.getElementById('id_province').value;
        const regionSelect = document.getElementById('id_region');
        regionSelect.innerHTML = '<option value="">---------</option>';

        if (provinceId) {
            fetch(`/api/regions-for-province/${provinceId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(region => {
                        const option = new Option(region.name, region.id);
                        regionSelect.add(option);
                    });
                });
        }
    }

    function updateLfas() {
        const regionId = document.getElementById('id_region').value;
        const lfaSelect = document.getElementById('id_local_federation');
        lfaSelect.innerHTML = '<option value="">---------</option>';

        if (regionId) {
            fetch(`/api/lfas-for-region/${regionId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(lfa => {
                        const option = new Option(lfa.name, lfa.id);
                        lfaSelect.add(option);
                    });
                });
        }
    }

    function updateClubs() {
        const lfaId = document.getElementById('id_local_federation').value;
        const clubSelect = document.getElementById('id_club');
        clubSelect.innerHTML = '<option value="">---------</option>';

        if (lfaId) {
            fetch(`/api/clubs-for-lfa/${lfaId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(club => {
                        const option = new Option(club.name, club.id);
                        clubSelect.add(option);
                    });
                });
        }
    }
    
    function toggleIdFields() {
        if(!idDocumentType) return;
        if (idDocumentType.value === 'ID') {
            saIdContainer.style.display = 'block';
            passportContainer.style.display = 'none';
            dobGenderManualRow.style.display = 'none';
        } else if (idDocumentType.value === 'PP') {
            saIdContainer.style.display = 'none';
            passportContainer.style.display = 'block';
            dobGenderManualRow.style.display = 'block';
        } else {
            saIdContainer.style.display = 'none';
            passportContainer.style.display = 'none';
            dobGenderManualRow.style.display = 'none';
        }
    }

    if (organizationType) {
        organizationType.addEventListener('change', toggleFields);
        toggleFields();
    }
    if (idDocumentType) {
        idDocumentType.addEventListener('change', toggleIdFields);
        toggleIdFields();
    }
    if(document.getElementById('id_province')) {
        document.getElementById('id_province').addEventListener('change', updateRegions);
    }
    if(document.getElementById('id_region')) {
        document.getElementById('id_region').addEventListener('change', updateLfas);
    }
    if(document.getElementById('id_local_federation')) {
        document.getElementById('id_local_federation').addEventListener('change', updateClubs);
    }


    const idNumberField = document.getElementById('id_id_number');
    const idValidationMessage = document.getElementById('id-validation-message');
    const dobField = document.getElementById('id_date_of_birth');
    const genderField = document.getElementById('id_gender');

    if (idNumberField && idValidationMessage) {
        idNumberField.addEventListener('input', function() {
            const idNumber = idNumberField.value;
            const validationResult = validateSAIDNumber(idNumber);

            if (validationResult.isValid) {
                idValidationMessage.textContent = '';
                idValidationMessage.classList.remove('text-danger');
                idValidationMessage.classList.add('text-success');
                idValidationMessage.textContent = `Valid ID. DOB: ${formatDateYMD(validationResult.dateOfBirth)}, Gender: ${validationResult.gender}`;
                if(dobField) dobField.value = formatDateYMD(validationResult.dateOfBirth);
                if(genderField) genderField.value = validationResult.gender;
            } else {
                idValidationMessage.textContent = '';
                idValidationMessage.classList.remove('text-success');
                idValidationMessage.classList.add('text-danger');
                idValidationMessage.textContent = validationResult.errorMessage;
                if(dobField) dobField.value = '';
                if(genderField) genderField.value = '';
            }
        });
    }

    const emailField = document.getElementById('id_email');
    const emailValidationMessage = document.getElementById('email-validation-message');

    if(emailField && emailValidationMessage){
        emailField.addEventListener('input', function() {
            const email = emailField.value;
            if (!email) {
                emailValidationMessage.textContent = '';
            } else {
                fetch(`/ajax/check-email/?email=${email}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            emailValidationMessage.textContent = 'Email already exists.';
                            emailValidationMessage.classList.remove('text-success');
                            emailValidationMessage.classList.add('text-danger');
                        } else {
                            emailValidationMessage.textContent = 'Email is available.';
                            emailValidationMessage.classList.remove('text-danger');
                            emailValidationMessage.classList.add('text-success');
                        }
                    });
            }
        });
    }
});

function validateSAIDNumber(idNumber) {
    const result = {
        isValid: false,
        errorMessage: null,
        citizenship: null,
        gender: null,
        dateOfBirth: null
    };

    if (!idNumber) {
        result.errorMessage = "ID number is required";
        return result;
    }

    if (!/^\d+$/.test(idNumber)) {
        result.errorMessage = "ID number must contain only digits";
        return result;
    }

    if (idNumber.length !== 13) {
        result.errorMessage = "ID number must be exactly 13 digits";
        return result;
    }

    try {
        const year = parseInt(idNumber.substring(0, 2));
        const month = parseInt(idNumber.substring(2, 4));
        const day = parseInt(idNumber.substring(4, 6));

        const currentYear = new Date().getFullYear() % 100;
        let fullYear = year > currentYear ? 1900 + year : 2000 + year;

        if (month < 1 || month > 12) {
            result.errorMessage = "ID number contains invalid month";
            return result;
        }

        const lastDay = new Date(fullYear, month, 0).getDate();
        if (day < 1 || day > lastDay) {
            result.errorMessage = "ID number contains invalid day";
            return result;
        }

        const dob = new Date(fullYear, month - 1, day);
        result.dateOfBirth = dob;

        const genderDigits = parseInt(idNumber.substring(6, 10));
        result.gender = genderDigits >= 5000 ? "M" : "F";

        const citizenshipDigit = parseInt(idNumber.charAt(10));
        result.citizenship = citizenshipDigit === 0 ? "SA Citizen" : "Permanent Resident";

        let oddSum = 0;
        let evenDigits = "";

        for (let i = 0; i < idNumber.length - 1; i++) {
            const digit = parseInt(idNumber.charAt(i));
            if (i % 2 === 0) {
                oddSum += digit;
            } else {
                evenDigits += digit;
            }
        }

        const doubledEven = parseInt(evenDigits) * 2;
        const evenSum = doubledEven.toString().split('').reduce((sum, digit) => sum + parseInt(digit), 0);

        const total = oddSum + evenSum;
        const checkDigit = (10 - (total % 10)) % 10;

        if (checkDigit === parseInt(idNumber.charAt(12))) {
            result.isValid = true;
        } else {
            result.errorMessage = "ID number has an invalid checksum digit.";
        }

        return result;
    } catch (e) {
        console.error("Error validating SA ID number:", e);
        result.errorMessage = `Error validating ID number: ${e.message}`;
        return result;
    }
}

function formatDateYMD(date) {
    if (!date) return '';

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}
