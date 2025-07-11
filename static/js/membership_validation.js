// Membership validation functions

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
    // If valid format, run the full validation
    const result = validateSAID(input.value);
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
        feedbackElement.textContent = result.message;
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

// SA ID validation function
function validateSAID(idNumber) {
  if (!idNumber || idNumber.length !== 13 || !/^\d+$/.test(idNumber)) {
    return { isValid: false, message: "ID number must be 13 digits" };
  }

  const year = idNumber.substring(0, 2);
  const month = idNumber.substring(2, 4);
  const day = idNumber.substring(4, 6);

  // Validate month (1-12)
  if (parseInt(month) < 1 || parseInt(month) > 12) {
    return { isValid: false, message: "ID contains invalid month" };
  }

  // Validate day (1-31, depending on month)
  const dayNum = parseInt(day);
  if (dayNum < 1 || dayNum > 31) {
    return { isValid: false, message: "ID contains invalid day" };
  }

  // Check days in month
  const daysInMonth = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const monthNum = parseInt(month);

  // Adjust February for leap years
  const currentYear = new Date().getFullYear() % 100;
  const fullYear = parseInt(year) > currentYear ? 1900 + parseInt(year) : 2000 + parseInt(year);

  if (monthNum === 2 && ((fullYear % 4 === 0 && fullYear % 100 !== 0) || fullYear % 400 === 0)) {
    daysInMonth[2] = 29;
  }

  if (dayNum > daysInMonth[monthNum]) {
    return { isValid: false, message: "ID contains invalid day for month" };
  }

  const birthDate = new Date(fullYear, parseInt(month) - 1, parseInt(day));
  if (
    birthDate.getFullYear() !== fullYear ||
    birthDate.getMonth() + 1 !== parseInt(month) ||
    birthDate.getDate() !== parseInt(day)
  ) {
    return { isValid: false, message: "ID contains invalid date" };
  }

  // Validate checksum using Luhn algorithm
  let sum = 0;
  let alternate = false;
  for (let i = idNumber.length - 1; i >= 0; i--) {
    let n = parseInt(idNumber.substring(i, i + 1));
    if (alternate) {
      n *= 2;
      if (n > 9) {
        n = (n % 10) + 1;
      }
    }
    sum += n;
    alternate = !alternate;
  }

  // Check if the sum is divisible by 10
  if (sum % 10 !== 0) {
    return { isValid: false, message: "ID number has invalid checksum" };
  }

  const genderDigits = parseInt(idNumber.substring(6, 10));
  const gender = genderDigits >= 5000 ? 'M' : 'F';
  const genderText = gender === 'M' ? 'Male' : 'Female';

  return {
    isValid: true,
    message: "Valid ID number",
    dateOfBirth: birthDate.toISOString().split('T')[0],
    gender: gender,
    genderText: genderText
  };
}
