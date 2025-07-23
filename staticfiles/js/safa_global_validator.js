function validateSAID(idNumber) {
    if (!idNumber || idNumber.length !== 13 || !/^\d+$/.test(idNumber)) {
        return { isValid: false, message: "ID number must be 13 digits and contain only numbers." };
    }

    let sum = 0;
    for (let i = 0; i < 12; i++) {
        let digit = parseInt(idNumber.charAt(i));
        if ((i % 2) === 0) {
            sum += digit;
        } else {
            let evenDigit = digit * 2;
            if (evenDigit > 9) {
                evenDigit = evenDigit - 9;
            }
            sum += evenDigit;
        }
    }
    const lastDigit = parseInt(idNumber.charAt(12));
    const checksum = (10 - (sum % 10)) % 10;

    if (checksum !== lastDigit) {
        return { isValid: false, message: "Invalid ID number (Luhn check failed)." };
    }

    const year = idNumber.substring(0, 2);
    const month = idNumber.substring(2, 4);
    const day = idNumber.substring(4, 6);
    
    const currentYear = new Date().getFullYear() % 100;
    const birthYear = parseInt(year);
    const fullYear = birthYear > currentYear ? 1900 + birthYear : 2000 + birthYear;
    
    const birthDate = new Date(fullYear, parseInt(month) - 1, parseInt(day));
    if (
        birthDate.getFullYear() !== fullYear || 
        birthDate.getMonth() + 1 !== parseInt(month) || 
        birthDate.getDate() !== parseInt(day)
    ) {
        return { isValid: false, message: "ID contains invalid date" };
    }
    
    const genderDigits = parseInt(idNumber.substring(6, 10));
    const gender = genderDigits >= 5000 ? 'M' : 'F';
    const genderText = gender === 'M' ? 'Male' : 'Female';
    
    const formattedDate = birthDate.toISOString().split('T')[0];
    const displayDate = new Intl.DateTimeFormat('en-ZA', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    }).format(birthDate);
    
    return {
        isValid: true,
        message: "Valid ID number",
        dateOfBirth: formattedDate,
        displayDate: displayDate,
        gender: gender,
        genderText: genderText
    };
}

function validateName(name) {
    if (!name || name.length < 3 || !/^[a-zA-Z]+$/.test(name)) {
        return { isValid: false, message: "Name must be at least 3 letters and contain only letters." };
    }
    return { isValid: true };
}
