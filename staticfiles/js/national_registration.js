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
            age: new Date().getFullYear() - fullYear,
            documentType: 'South African ID'
        }
    };
}

function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    return age;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('National Registration JS loaded');
    
    const form = document.querySelector('form');
    const idInput = document.getElementById('id_national_id_number');
    const docTypeSelect = document.getElementById('id_id_document_type');
    
    console.log('Form found:', !!form);
    console.log('ID Input found:', !!idInput);
    console.log('Doc Type Select found:', !!docTypeSelect);
    
    if (idInput) {
        console.log('ID Input name:', idInput.name);
        console.log('ID Input id:', idInput.id);
    }
    
    // COMPLETELY DISABLE ALL JAVASCRIPT INTERFERENCE
    console.log('ALL JAVASCRIPT DISABLED - FORM SHOULD WORK');
});
