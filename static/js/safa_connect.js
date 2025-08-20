function validateSAID(idNumber) {
    if (typeof idNumber !== 'string' || !/^\d{13}$/.test(idNumber)) {
        return { isValid: false, message: 'ID number must be 13 digits.' };
    }

    let year = parseInt(idNumber.substring(0, 2), 10);
    const month = parseInt(idNumber.substring(2, 4), 10);
    const day = parseInt(idNumber.substring(4, 6), 10);

    const currentYear = new Date().getFullYear() % 100;
    year = year <= currentYear ? 2000 + year : 1900 + year;

    if (month < 1 || month > 12 || day < 1 || day > 31) {
        return { isValid: false, message: 'Invalid date of birth in ID.' };
    }

    const genderDigit = parseInt(idNumber.substring(6, 10), 10);
    const gender = genderDigit >= 5000 ? 'M' : 'F';
    const genderText = gender === 'M' ? 'Male' : 'Female';

    let a = 0;
    let b = 0;
    for (let i = 0; i < 12; i++) {
        const digit = parseInt(idNumber.charAt(i), 10);
        if (i % 2 === 0) {
            a += digit;
        } else {
            b = b * 10 + digit;
        }
    }
    b = b * 2;
    let c = 0;
    while (b > 0) {
        c += b % 10;
        b = Math.floor(b / 10);
    }

    const checksum = (a + c) % 10;
    const lastDigit = parseInt(idNumber.charAt(12), 10);
    const isValid = (10 - checksum) % 10 === lastDigit;

    if (!isValid) {
        return { isValid: false, message: 'Invalid ID number (checksum fail).' };
    }

    const dateOfBirth = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    return {
        isValid: true,
        message: 'Valid ID number.',
        dateOfBirth: dateOfBirth,
        displayDate: dateOfBirth,
        gender: gender,
        genderText: genderText,
    };
}

function validateName(name) {
    if (typeof name !== 'string' || name.length < 2) {
        return { isValid: false, message: 'Name must be at least 2 characters.' };
    }
    if (!/^[a-zA-Z\s'-]+$/.test(name)) {
        return { isValid: false, message: 'Name contains invalid characters.' };
    }
    return { isValid: true, message: '' };
}
