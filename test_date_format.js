// Test how the date is formatted in JavaScript with toLocaleDateString('en-ZA')
const testDate = new Date(1968, 4, 31); // May is 4 (0-indexed)
console.log(`Date object: ${testDate}`);
console.log(`toLocaleDateString('en-ZA'): ${testDate.toLocaleDateString('en-ZA')}`);

// Test with the ID number from the issue
const idNumber = '6805315146080';
const year = parseInt(idNumber.substring(0, 2));
const month = parseInt(idNumber.substring(2, 4));
const day = parseInt(idNumber.substring(4, 6));

const currentYear = new Date().getFullYear() % 100;
const fullYear = year > currentYear ? 1900 + year : 2000 + year;

const date = new Date(fullYear, month - 1, day);
console.log(`ID number: ${idNumber}`);
console.log(`Extracted date components: year=${year}, month=${month}, day=${day}`);
console.log(`Full year: ${fullYear}`);
console.log(`Date object: ${date}`);
console.log(`toLocaleDateString('en-ZA'): ${date.toLocaleDateString('en-ZA')}`);
console.log(`getDate(): ${date.getDate()}`);
console.log(`getMonth(): ${date.getMonth()}`);
console.log(`getFullYear(): ${date.getFullYear()}`);

// Test with a different locale
console.log(`toLocaleDateString('en-US'): ${date.toLocaleDateString('en-US')}`);
