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

        // SA-specific Luhn Algorithm
        let odd_sum = 0;
        for (let i = 0; i < 12; i += 2) {
            odd_sum += parseInt(idNumber[i], 10);
        }

        let even_digits_str = "";
        for (let i = 1; i < 12; i += 2) {
            even_digits_str += idNumber[i];
        }
        const even_doubled = parseInt(even_digits_str, 10) * 2;

        let even_sum = 0;
        for (const digit of String(even_doubled)) {
            even_sum += parseInt(digit, 10);
        }

        const total_sum = odd_sum + even_sum;
        const check_digit = (10 - (total_sum % 10)) % 10;

        if (check_digit !== parseInt(idNumber[12], 10)) {
            result.errorMessage = "Invalid ID number (checksum failed).";
            return result;
        }

        result.isValid = true;
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
