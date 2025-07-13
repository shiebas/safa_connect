// Membership validation functions

// GLOBAL SOUTH AFRICAN ID VALIDATION
// This is the single source of truth for SA ID validation across the application
const SAFA = window.SAFA || {};
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
  populateFields: function(idNumber, dobField, genderField) {
    const result = this.validateSAID(idNumber);
    if (result.isValid) {
      if (dobField) dobField.value = result.dateOfBirth;
      if (genderField) genderField.value = result.gender;
    }
    return result;
  }
};

// Make the validator available globally
window.SAFA = SAFA;

// Name validation function
function validateNameField(input) {
  // Allow letters, spaces, hyphens, and apostrophes, but no numbers or other special characters
  const namePattern = /^[A-Za-z\s\-']+$/;

  if (!input.value || input.value.trim() === '') {
    input.setCustomValidity("Name is required");
  } else if (input.value.length < 3) {
    input.setCustomValidity("Name must be at least 3 characters long");
  } else if (!namePattern.test(input.value)) {
    input.setCustomValidity("Name must contain only letters, spaces, hyphens, and apostrophes (no numbers)");
  } else {
    input.setCustomValidity("");
  }
}

// ID validation function
function validateIdField(input) {
  // Only allow exactly 13 digits
  const idPattern = /^\d{13}$/;
  const feedbackElement = document.getElementById('id-validation-feedback');

  if (!input.value || input.value.trim() === '') {
    input.setCustomValidity("ID number is required");
    if (feedbackElement) {
      feedbackElement.textContent = "ID number is required";
      feedbackElement.className = "form-text text-danger";
    }
  } else if (!idPattern.test(input.value)) {
    input.setCustomValidity("ID number must be exactly 13 digits (numbers only)");
    if (feedbackElement) {
      feedbackElement.textContent = "ID number must be exactly 13 digits (numbers only)";
      feedbackElement.className = "form-text text-danger";
    }
  } else {
    // If valid format, run the full validation using the global validator
    const result = SAFA.IDValidator.validateSAID(input.value);

    // Try to auto-populate DOB and gender fields if they exist
    const dobField = document.getElementById('id_date_of_birth');
    const genderField = document.getElementById('id_gender');
    if (result.isValid && dobField && genderField) {
      SAFA.IDValidator.populateFields(input.value, dobField, genderField);
    }

    if (!result.isValid) {
      input.setCustomValidity(result.message);
      if (feedbackElement) {
        feedbackElement.textContent = result.message;
        feedbackElement.className = "form-text text-danger";
      }
    } else {
      input.setCustomValidity("");
      // Update the validation feedback message
      if (feedbackElement) {
        feedbackElement.textContent = result.message + " (" + result.formattedDateOfBirth + ", " + result.genderText + ")";
        feedbackElement.className = "form-text text-success";
      }
    }
  }
}

// Email validation function
function validateEmailField(input) {
  const emailPattern = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  const feedbackId = input.id + '-feedback';
  let feedbackElement = document.getElementById(feedbackId);

  // Create feedback element if it doesn't exist
  if (!feedbackElement) {
    feedbackElement = document.createElement('div');
    feedbackElement.id = feedbackId;
    feedbackElement.className = 'form-text';
    input.parentNode.appendChild(feedbackElement);
  }

  if (!input.value) {
    input.setCustomValidity("Email address is required");
    feedbackElement.textContent = "Email address is required";
    feedbackElement.className = "form-text text-danger";
    return false;
  } else if (!emailPattern.test(input.value)) {
    input.setCustomValidity("Please enter a valid email address");
    feedbackElement.textContent = "Please enter a valid email address";
    feedbackElement.className = "form-text text-danger";
    return false;
  } else {
    input.setCustomValidity("");
    feedbackElement.textContent = "Valid email address";
    feedbackElement.className = "form-text text-success";
    return true;
  }
}

// SA ID validation function is now provided by the global SAFA.IDValidator.validateSAID
// This wrapper is kept for backward compatibility
function validateSAID(idNumber) {
  return SAFA.IDValidator.validateSAID(idNumber);
}
