/**
 * SAFA Global Validators
 *
 * This file contains validation functions that are used across the entire application.
 * Include this file in templates that need validation functionality.
 */

// Create global SAFA namespace if it doesn't exist
const SAFA = window.SAFA || {};

// SA ID Validator
SAFA.IDValidator = {
  // Validate SA ID number and extract personal information
  validateSAID: function(idNumber) {
    if (!idNumber || idNumber.length !== 13 || !/^\d+$/.test(idNumber)) {
      return { isValid: false, message: "ID number must be 13 digits" };
    }

    // Extract date components
    const yearStr = idNumber.substring(0, 2);
    const monthStr = idNumber.substring(2, 4);
    const dayStr = idNumber.substring(4, 6);

    // Convert to integers
    const monthNum = parseInt(monthStr);
    const dayNum = parseInt(dayStr);

    // Validate month (1-12)
    if (monthNum < 1 || monthNum > 12) {
      return { isValid: false, message: "ID contains invalid month" };
    }

    // Validate day (1-31, depending on month)
    if (dayNum < 1 || dayNum > 31) {
      return { isValid: false, message: "ID contains invalid day" };
    }

    // Determine century for the year
    const currentYear = new Date().getFullYear() % 100;
    const yearNum = parseInt(yearStr);
    const fullYear = yearNum > currentYear ? 1900 + yearNum : 2000 + yearNum;

    // Check days in month
    const daysInMonth = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    // Adjust February for leap years
    if (monthNum === 2 && ((fullYear % 4 === 0 && fullYear % 100 !== 0) || fullYear % 400 === 0)) {
      daysInMonth[2] = 29;
    }

    if (dayNum > daysInMonth[monthNum]) {
      return { isValid: false, message: "ID contains invalid day for month" };
    }

    // Format the date strings properly for consistent representation
    const formattedMonth = monthStr.padStart(2, '0');
    const formattedDay = dayStr.padStart(2, '0');

    // Create ISO date string format (YYYY-MM-DD)
    const dateStr = `${fullYear}-${formattedMonth}-${formattedDay}`;

    // Create a Date object to verify date validity
    const birthDate = new Date(dateStr);

    // Extra validation for date consistency
    if (birthDate.getFullYear() !== fullYear ||
        birthDate.getMonth() + 1 !== parseInt(formattedMonth) ||
        birthDate.getDate() !== parseInt(formattedDay)) {
      return { isValid: false, message: "ID contains invalid date" };
    }

    // Validate Luhn algorithm checksum
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
    if (checkDigit !== parseInt(idNumber.charAt(12))) {
      return { isValid: false, message: "ID number has an invalid checksum digit" };
    }

    // Extract gender from the ID number
    const genderDigits = parseInt(idNumber.substring(6, 10));
    const gender = genderDigits >= 5000 ? 'M' : 'F';
    const genderText = gender === 'M' ? 'Male' : 'Female';

    return {
      isValid: true,
      message: "Valid ID number",
      dateOfBirth: dateStr,
      gender: gender,
      genderText: genderText,
      // Also include a formatted date string that can be displayed to users
      formattedDateOfBirth: birthDate.toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    };
  },

  // Populate form fields based on ID validation result
  populateFields: function(idNumber, dobField, genderField, countryField) {
    const result = this.validateSAID(idNumber);
    if (result.isValid) {
      if (dobField) dobField.value = result.dateOfBirth;
      if (genderField) genderField.value = result.gender;
      if (countryField) countryField.value = 'ZAF';  // Set country to South Africa
    }
    return result;
  }
};

// Email validator
SAFA.EmailValidator = {
  validate: function(email) {
    const emailPattern = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
    return {
      isValid: emailPattern.test(email),
      message: emailPattern.test(email) ? "Valid email address" : "Please enter a valid email address"
    };
  }
};

// Name validator
SAFA.NameValidator = {
  validate: function(name) {
    const namePattern = /^[A-Za-z\s\-']+$/;

    if (!name || name.trim() === '') {
      return { isValid: false, message: "Name is required" };
    } else if (name.length < 3) {
      return { isValid: false, message: "Name must be at least 3 characters long" };
    } else if (!namePattern.test(name)) {
      return { isValid: false, message: "Name must contain only letters, spaces, hyphens, and apostrophes" };
    }

    return { isValid: true, message: "Valid name" };
  }
};

// Make the validators available globally
window.SAFA = SAFA;
