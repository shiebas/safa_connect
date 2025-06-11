document.addEventListener('DOMContentLoaded', function() {
    // Initialize form sections
    const formSections = document.querySelectorAll('.form-section');
    const formSteps = [];
    
    // Create step indicator
    const stepIndicator = document.createElement('div');
    stepIndicator.className = 'step-indicator';
    const formContainer = document.querySelector('.registration-form');
    const formHeader = document.querySelector('.form-header');
    formContainer.insertBefore(stepIndicator, formHeader.nextSibling);
    
    // Convert sections to steps
    formSections.forEach((section, index) => {
        // Create a wrapper for the section
        const stepWrapper = document.createElement('div');
        stepWrapper.className = 'form-step';
        if (index === 0) stepWrapper.classList.add('active');
        
        // Create dot for step indicator
        const dot = document.createElement('div');
        dot.className = 'step-dot';
        if (index === 0) dot.classList.add('active');
        stepIndicator.appendChild(dot);
        
        // Move the section into the wrapper
        section.parentNode.insertBefore(stepWrapper, section);
        stepWrapper.appendChild(section);
        
        // Add navigation buttons
        const navigation = document.createElement('div');
        navigation.className = 'step-navigation';
        
        if (index > 0) {
            const prevButton = document.createElement('button');
            prevButton.type = 'button';
            prevButton.className = 'btn btn-prev btn-step';
            prevButton.innerHTML = '<i class="fas fa-arrow-left me-2"></i>Previous';
            prevButton.addEventListener('click', () => goToStep(index - 1));
            navigation.appendChild(prevButton);
        } else {
            // Empty div for spacing
            const spacer = document.createElement('div');
            navigation.appendChild(spacer);
        }
        
        if (index < formSections.length - 1) {
            const nextButton = document.createElement('button');
            nextButton.type = 'button';
            nextButton.className = 'btn btn-next btn-step';
            nextButton.innerHTML = 'Next<i class="fas fa-arrow-right ms-2"></i>';
            nextButton.addEventListener('click', () => {
                if (validateStep(index)) {
                    goToStep(index + 1);
                }
            });
            navigation.appendChild(nextButton);
        } else {
            // For the last step, we'll use the submit button that already exists
            const spacer = document.createElement('div');
            navigation.appendChild(spacer);
        }
        
        stepWrapper.appendChild(navigation);
        formSteps.push(stepWrapper);
    });
    
    // Hide the main submit button (we'll show it only on the last step)
    const submitButton = document.querySelector('.text-center .btn-submit');
    const submitContainer = submitButton.parentNode;
    submitContainer.style.display = 'none';
    
    // Modify the last step's navigation to include the submit button
    const lastNavigation = formSteps[formSteps.length - 1].querySelector('.step-navigation');
    const submitClone = submitButton.cloneNode(true);
    lastNavigation.appendChild(submitClone);
    
    // Function to navigate between steps
    function goToStep(stepIndex) {
        // Update step classes
        formSteps.forEach((step, idx) => {
            step.classList.remove('active');
            const dot = stepIndicator.children[idx];
            dot.classList.remove('active');
            
            if (idx < stepIndex) {
                dot.classList.add('completed');
            } else {
                dot.classList.remove('completed');
            }
        });
        
        formSteps[stepIndex].classList.add('active');
        stepIndicator.children[stepIndex].classList.add('active');
        
        // Scroll to top of form
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Basic validation for each step
    function validateStep(stepIndex) {
        const currentStep = formSteps[stepIndex];
        const requiredFields = currentStep.querySelectorAll('input[required], select[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                
                // Add a shake animation to highlight the field
                field.animate([
                    { transform: 'translateX(0)' },
                    { transform: 'translateX(-5px)' },
                    { transform: 'translateX(5px)' },
                    { transform: 'translateX(-5px)' },
                    { transform: 'translateX(0)' }
                ], {
                    duration: 300,
                    iterations: 1
                });
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        if (!isValid) {
            // Highlight the first invalid field
            const firstInvalid = currentStep.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.focus();
            }
        }
        
        return isValid;
    }
    
    // Add event listeners to remove validation errors when user types
    document.querySelectorAll('input, select').forEach(field => {
        field.addEventListener('input', () => {
            if (field.value.trim()) {
                field.classList.remove('is-invalid');
            }
        });
    });
    
    // Hide the original submit button container
    document.querySelector('form .text-center').style.display = 'none';
});