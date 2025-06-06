$(document).ready(function() {
    const form = $('form[method="post"]');
    const idNumberField = $('#' + form.data('id-number-id'));
    const countryField = $('#' + form.data('country-id'));
    const dobField = $('#' + form.data('dob-id'));
    const genderField = $('#' + form.data('gender-id'));
    const idDocTypeField = $('#' + form.data('id-doc-type-id'));

    const idNumberBox = $('#id_number_box');
    const passportBox = $('#passport_box');
    const documentBox = $('#document_box');

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
        for (var i = 0; i < 12; i++) {
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

        if (selectedDocType === 'ID') {
            idNumberBox.show();
            passportBox.hide();
            documentBox.hide();
        } else if (selectedDocType === 'PP') {
            idNumberBox.hide();
            passportBox.show();
            documentBox.show();
        } else {
            idNumberBox.show();
            passportBox.show();
            documentBox.show();
        }
    }

    function handleIDNumberChange() {
        let idNumber = idNumberField.val();
        const country = countryField.val();
        const selectedDocType = idDocTypeField.val();

        if (selectedDocType !== 'ID') {
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
            return;
        }

        let countryCode = '';
        if (country) {
            const selectedOption = $('#' + form.data('country-id') + ' option:selected');
            const optionText = selectedOption.text();
            const codeMatch = optionText.match(/\(([A-Z]{3})\)/);
            if (codeMatch) {
                countryCode = codeMatch[1];
            }
        }

        if (countryCode === 'RSA') {
            countryCode = 'ZAF';
        }

        if (countryCode === 'ZAF') {
            idNumberField.attr('maxlength', '13');
            if (idNumber.length > 13) {
                idNumber = idNumber.substring(0, 13);
                idNumberField.val(idNumber);
            }
        } else if (countryCode === 'NAM') {
            idNumberField.attr('maxlength', '11');
        } else if (countryCode === 'LSO') {
            idNumberField.attr('maxlength', '10');
        } else {
            idNumberField.attr('maxlength', '20');
        }

        if (countryCode === 'ZAF' && idNumber && idNumber.length === 13) {
            const validationResult = validateSouthAfricanID(idNumber);

            if (validationResult) {
                dobField.prop('disabled', true);
                genderField.prop('disabled', true);

                const date = validationResult.dateOfBirth;
                const yyyy = date.getFullYear();
                const mm = String(date.getMonth() + 1).padStart(2, '0');
                const dd = String(date.getDate()).padStart(2, '0');
                const formattedDate = yyyy + '-' + mm + '-' + dd;
                dobField.val(formattedDate);
                genderField.val(validationResult.gender);
            } else {
                dobField.prop('disabled', false);
                genderField.prop('disabled', false);
            }
        } else {
            dobField.prop('disabled', false);
            genderField.prop('disabled', false);
        }
    }

    idNumberField.on('input', handleIDNumberChange);
    countryField.on('change', handleIDNumberChange);
    idDocTypeField.on('change', function() {
        handleDocumentTypeChange();
        handleIDNumberChange();
    });

    handleDocumentTypeChange();
    handleIDNumberChange();
});