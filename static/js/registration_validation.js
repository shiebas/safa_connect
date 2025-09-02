// Version: 1.1 - Age verification modal handling for SAFA Connect registration
// This script handles age verification for public registrations only
console.log('🚀 SCRIPT LOADED - registration_validation.js v1.1');

// Age verification modal handling for SAFA Connect registration
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Age verification script loaded');
    console.log('🔍 Page URL:', window.location.href);
    
    // Check if this is a club admin registration (no age verification needed)
    const isClubAdminRegistration = document.querySelector('[data-is-club-admin]') !== null;
    console.log('🔍 Is club admin registration:', isClubAdminRegistration);
    console.log('🔍 Data attribute found:', document.querySelector('[data-is-club-admin]'));
    
    // Debug: Check all elements with data attributes
    const allDataElements = document.querySelectorAll('[data-is-club-admin]');
    console.log('🔍 All data-is-club-admin elements:', allDataElements);
    
    if (isClubAdminRegistration) {
        console.log('🔍 Club admin registration detected, showing form immediately');
        // For club admin registrations, show the form immediately
        document.getElementById('registrationContainer').style.display = 'block';
        return;
    }
    
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('❌ Bootstrap is not loaded. Cannot show age verification modal.');
        // Fallback: show form without age verification
        document.getElementById('registrationContainer').style.display = 'block';
        return;
    }
    
    console.log('✅ Bootstrap is available');
    
    // Check if the modal element exists
    const modalElement = document.getElementById('ageVerificationModal');
    if (!modalElement) {
        console.error('❌ Age verification modal element not found.');
        console.log('🔍 All modal elements on page:', document.querySelectorAll('.modal'));
        console.log('🔍 All elements with ageVerificationModal ID:', document.querySelectorAll('#ageVerificationModal'));
        // Fallback: show form without age verification
        document.getElementById('registrationContainer').style.display = 'block';
        return;
    }
    
    console.log('✅ Modal element found:', modalElement);
    console.log('🔍 Modal classes:', modalElement.className);
    console.log('🔍 Modal style display:', modalElement.style.display);
    
    // Store modal instance globally to prevent garbage collection
    window.ageVerificationModalInstance = null;
    
    // AGGRESSIVE: Override any Bootstrap modal methods that might hide the modal
    const originalHide = bootstrap.Modal.prototype.hide;
    bootstrap.Modal.prototype.hide = function() {
        console.log('🔍 Bootstrap Modal.hide() called');
        // Only allow hiding if this is our age verification modal and user has made a choice
        if (this._element && this._element.id === 'ageVerificationModal') {
            if (sessionStorage.getItem('safa_age_verified') === null) {
                console.log('⚠️ Preventing Bootstrap Modal.hide() for age verification modal');
                return;
            }
        }
        // Call original method for other modals
        return originalHide.call(this);
    };
    
    // Wait a bit to ensure Bootstrap is fully initialized
    setTimeout(function() {
        try {
            console.log('🔍 Initializing age verification modal...');
            
            // Show age verification modal (only for public registrations)
            const ageVerificationModal = new bootstrap.Modal(modalElement, {
                backdrop: 'static',
                keyboard: false
            });
            
            // Store instance globally
            window.ageVerificationModalInstance = ageVerificationModal;
            
            console.log('✅ Modal instance created');
            
            // Add event listeners BEFORE showing the modal
            const yesButton = document.getElementById('yesOver18');
            const noButton = document.getElementById('noUnder18');
            
            if (yesButton) {
                yesButton.addEventListener('click', function() {
                    console.log('🔍 Yes button clicked');
                    // Hide the age verification modal
                    ageVerificationModal.hide();
                    
                    // Show the registration form
                    document.getElementById('registrationContainer').style.display = 'block';
                    
                    // Store in session storage that user confirmed they are 18+
                    sessionStorage.setItem('safa_age_verified', 'true');
                    console.log('✅ Age verified, form shown');
                });
            }
            
            if (noButton) {
                noButton.addEventListener('click', function() {
                    console.log('🔍 No button clicked');
                    // Hide the age verification modal
                    ageVerificationModal.hide();
                    
                    // Show the thank you modal
                    const thankYouModal = new bootstrap.Modal(document.getElementById('thankYouModal'), {
                        backdrop: 'static',
                        keyboard: false
                    });
                    thankYouModal.show();
                    
                    // Store in session storage that user is under 18
                    sessionStorage.setItem('safa_age_verified', 'false');
                    console.log('✅ Under 18 confirmed, thank you modal shown');
                });
            }
            
            // Handle thank you modal close - redirect to home
            const thankYouModalElement = document.getElementById('thankYouModal');
            if (thankYouModalElement) {
                thankYouModalElement.addEventListener('hidden.bs.modal', function() {
                    console.log('🔍 Thank you modal closed, redirecting to home');
                    // Redirect to home page
                    window.location.href = '/';
                });
            }
            
            // CRITICAL: Prevent modal from being hidden automatically
            modalElement.addEventListener('hide.bs.modal', function(e) {
                console.log('🔍 Modal hide event triggered');
                // Only allow hiding if user has made a choice
                if (sessionStorage.getItem('safa_age_verified') === null) {
                    console.log('⚠️ Preventing modal from being hidden automatically');
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
            
            // Also prevent hidden event
            modalElement.addEventListener('hidden.bs.modal', function(e) {
                console.log('🔍 Modal hidden event triggered');
                // Only allow hiding if user has made a choice
                if (sessionStorage.getItem('safa_age_verified') === null) {
                    console.log('⚠️ Preventing modal from being hidden automatically');
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
            
            // Show the modal AFTER setting up all event listeners
            ageVerificationModal.show();
            console.log('✅ Modal show() called');
            
            // Add manual fallback to ensure modal is visible
            setTimeout(function() {
                if (!modalElement.classList.contains('show')) {
                    console.log('⚠️ Modal not showing, trying manual fallback');
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                    modalElement.setAttribute('aria-hidden', 'false');
                    
                    // Also add backdrop
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    backdrop.id = 'manualBackdrop';
                    document.body.appendChild(backdrop);
                }
            }, 500);
            
            // Add periodic check to keep modal visible
            const modalVisibilityCheck = setInterval(function() {
                if (sessionStorage.getItem('safa_age_verified') !== null) {
                    // User has made a choice, stop checking
                    clearInterval(modalVisibilityCheck);
                    return;
                }
                
                if (!modalElement.classList.contains('show')) {
                    console.log('⚠️ Modal lost visibility, restoring...');
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                    modalElement.setAttribute('aria-hidden', 'false');
                    
                    // Ensure backdrop is visible
                    let backdrop = document.getElementById('manualBackdrop');
                    if (!backdrop) {
                        backdrop = document.createElement('div');
                        backdrop.className = 'modal-backdrop fade show';
                        backdrop.id = 'manualBackdrop';
                        document.body.appendChild(backdrop);
                    }
                }
            }, 1000); // Check every second
            
            console.log('✅ Modal initialization complete');
            
        } catch (error) {
            console.error('❌ Error initializing age verification modal:', error);
            // Fallback: show form without age verification
            document.getElementById('registrationContainer').style.display = 'block';
        }
    }, 200); // Increased delay to ensure Bootstrap is ready
    
    // Check if user has already verified their age in this session
    if (sessionStorage.getItem('safa_age_verified') === 'true') {
        console.log('🔍 User already verified age, showing form');
        // User already confirmed they are 18+, show registration form
        document.getElementById('registrationContainer').style.display = 'block';
    } else if (sessionStorage.getItem('safa_age_verified') === 'false') {
        console.log('🔍 User confirmed under 18, redirecting to home');
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

console.log('🚀 SCRIPT END - registration_validation.js v1.1');
