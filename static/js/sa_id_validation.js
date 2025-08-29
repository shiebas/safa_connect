/**
 * South African ID Number validation utility
 * Provides functions to validate SA ID numbers using the Luhn algorithm.
 */

/**
 * Validates a South African ID number using the Luhn algorithm.
 * @param {string} idNumber - The 13-digit SA ID number to validate
 * @returns {Object} Validation result object with is_valid, error_message, and extracted information
 */
function validateSAIDNumber(idNumber) {
    const result = {
        isValid: false,
        errorMessage: null,
        citizenship: null,
        gender: null,
        dateOfBirth: null
    };

    // Basic validation
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
        // Extract birth date components
        const year = parseInt(idNumber.substring(0, 2));
        const month = parseInt(idNumber.substring(2, 4));
        const day = parseInt(idNumber.substring(4, 6));

        // Determine century
        const currentYear = new Date().getFullYear() % 100;
        let fullYear = year > currentYear ? 1900 + year : 2000 + year;

        // Validate date components
        if (month < 1 || month > 12) {
            result.errorMessage = "ID number contains invalid month";
            return result;
        }

        // Check days in month
        const lastDay = new Date(fullYear, month, 0).getDate();
        if (day < 1 || day > lastDay) {
            result.errorMessage = "ID number contains invalid day";
            return result;
        }

        // Create date object
        const dob = new Date(fullYear, month - 1, day);
        result.dateOfBirth = dob;

        // Extract gender
        const genderDigits = parseInt(idNumber.substring(6, 10));
        result.gender = genderDigits >= 5000 ? "M" : "F";

        // Extract citizenship
        const citizenshipDigit = parseInt(idNumber.charAt(10));
        result.citizenship = citizenshipDigit === 0 ? "SA Citizen" : "Permanent Resident";

        // Luhn algorithm validation for South African ID
        // Using the standard algorithm for SA IDs:
        // 1. Add all digits in odd positions (1st, 3rd, 5th, etc.)
        // 2. Concatenate all digits in even positions (2nd, 4th, 6th, etc.)
        // 3. Multiply the result of step 2 by 2
        // 4. Add the digits of the result from step 3
        // 5. Add the result from step 4 to the result from step 1
        // 6. The check digit is (10 - (result % 10)) % 10

        let oddSum = 0;
        let evenDigits = "";

        // Process all digits except the check digit
        for (let i = 0; i < idNumber.length - 1; i++) {
            const digit = parseInt(idNumber.charAt(i));
            if (i % 2 === 0) {  // Odd position (1-indexed)
                oddSum += digit;
            } else {  // Even position (1-indexed)
                evenDigits += digit;
            }
        }

        // Double the even digits as a single number and sum its digits
        const doubledEven = parseInt(evenDigits) * 2;
        const evenSum = doubledEven.toString().split('').reduce((sum, digit) => sum + parseInt(digit), 0);

        // Calculate the total and check digit
        const total = oddSum + evenSum;
        const checkDigit = (10 - (total % 10)) % 10;

        // Compare with the actual check digit
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

/**
 * Formats a date object as YYYY-MM-DD
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string
 */
function formatDateYMD(date) {
    if (!date) return '';

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}
