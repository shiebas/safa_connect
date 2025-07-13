// Test the checksum validation for South African ID numbers

// Implementation from accounts/models.py
function validateChecksumAccounts(idNumber) {
    let oddSum = 0;
    let evenDigits = "";

    // Remember that positions are 0-indexed in code but 1-indexed in the algorithm description
    for (let i = 0; i < idNumber.length - 1; i++) {  // Exclude the check digit
        const digit = parseInt(idNumber[i]);
        if (i % 2 === 0) {  // Even position in 0-indexed (odd in 1-indexed)
            oddSum += digit;
        } else {  // Odd position in 0-indexed (even in 1-indexed)
            evenDigits += digit;
        }
    }

    // Double the even digits as a single number and sum its digits
    const doubledEven = parseInt(evenDigits) * 2;
    const evenSum = doubledEven.toString().split('').reduce((sum, digit) => sum + parseInt(digit), 0);

    // Calculate the total and check digit
    const total = oddSum + evenSum;
    const checkDigit = (10 - (total % 10)) % 10;

    return {
        valid: checkDigit === parseInt(idNumber[12]),
        expectedCheckDigit: checkDigit,
        actualCheckDigit: parseInt(idNumber[12])
    };
}

// Implementation from membership/models.py
function validateChecksumMembership(idNumber) {
    const digits = idNumber.split('').map(d => parseInt(d));
    let checksum = 0;

    for (let i = 0; i < digits.length; i++) {
        if (i % 2 === 0) {
            checksum += digits[i];
        } else {
            const doubled = digits[i] * 2;
            checksum += doubled < 10 ? doubled : (doubled - 9);
        }
    }

    return {
        valid: checksum % 10 === 0,
        checksum: checksum
    };
}

// Implementation from registration_form.js
function validateChecksumRegistration(idNumber) {
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

    return {
        valid: checkDigit === parseInt(idNumber[12]),
        expectedCheckDigit: checkDigit,
        actualCheckDigit: parseInt(idNumber[12])
    };
}

// Test with the provided ID numbers
const idNumbers = ['6805315146080', '6805315146081'];

console.log("Testing with accounts implementation:");
for (const idNumber of idNumbers) {
    const result = validateChecksumAccounts(idNumber);
    console.log(`ID number: ${idNumber}`);
    console.log(`Valid: ${result.valid}`);
    console.log(`Expected check digit: ${result.expectedCheckDigit}`);
    console.log(`Actual check digit: ${result.actualCheckDigit}`);
    console.log();
}

console.log("Testing with membership implementation:");
for (const idNumber of idNumbers) {
    const result = validateChecksumMembership(idNumber);
    console.log(`ID number: ${idNumber}`);
    console.log(`Valid: ${result.valid}`);
    console.log(`Checksum: ${result.checksum}`);
    console.log();
}

console.log("Testing with registration implementation:");
for (const idNumber of idNumbers) {
    const result = validateChecksumRegistration(idNumber);
    console.log(`ID number: ${idNumber}`);
    console.log(`Valid: ${result.valid}`);
    console.log(`Expected check digit: ${result.expectedCheckDigit}`);
    console.log(`Actual check digit: ${result.actualCheckDigit}`);
    console.log();
}
