// Age verification modal handling for SAFA Connect registration
document.addEventListener('DOMContentLoaded', function() {
    // Show age verification modal immediately when page loads
    const ageVerificationModal = new bootstrap.Modal(document.getElementById('ageVerificationModal'));
    ageVerificationModal.show();
    
    // Handle "Yes, I am 18+" button click
    document.getElementById('yesOver18').addEventListener('click', function() {
        // Hide the age verification modal
        ageVerificationModal.hide();
        
        // Show the registration form
        document.getElementById('registrationContainer').style.display = 'block';
        
        // Store in session storage that user confirmed they are 18+
        sessionStorage.setItem('safa_age_verified', 'true');
    });
    
    // Handle "No, I am under 18" button click
    document.getElementById('noUnder18').addEventListener('click', function() {
        // Hide the age verification modal
        ageVerificationModal.hide();
        
        // Show the thank you modal
        const thankYouModal = new bootstrap.Modal(document.getElementById('thankYouModal'));
        thankYouModal.show();
        
        // Store in session storage that user is under 18
        sessionStorage.setItem('safa_age_verified', 'false');
    });
    
    // Handle thank you modal close - redirect to home
    document.getElementById('thankYouModal').addEventListener('hidden.bs.modal', function() {
        // Redirect to home page
        window.location.href = '/';
    });
    
    // Check if user has already verified their age in this session
    if (sessionStorage.getItem('safa_age_verified') === 'true') {
        // User already confirmed they are 18+, show registration form
        document.getElementById('registrationContainer').style.display = 'block';
    } else if (sessionStorage.getItem('safa_age_verified') === 'false') {
        // User already confirmed they are under 18, redirect to home
        window.location.href = '/';
    }
    
    // Prevent form submission if user hasn't verified age
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(e) {
            if (sessionStorage.getItem('safa_age_verified') !== 'true') {
                e.preventDefault();
                alert('Please verify your age before proceeding with registration.');
                return false;
            }
        });
    }
});
