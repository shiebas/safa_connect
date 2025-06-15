/**
 * SAFA Registration Form Wizard
 * Handles multi-step form navigation for all registration flows
 */
function initFormWizard() {
    // Get all form sections
    const formSections = document.querySelectorAll('.form-section');
    if (!formSections.length) return;
    
    // Create step navigation container
    const formStepsContainer = document.createElement('div');
    formStepsContainer.className = 'form-steps mb-4';
    formStepsContainer.style.display = 'flex';
    formStepsContainer.style.justifyContent = 'space-between';
    formStepsContainer.style.position = 'sticky';
    formStepsContainer.style.top = '0';
    formStepsContainer.style.zIndex = '100';
    formStepsContainer.style.background = '#fff';
    formStepsContainer.style.padding = '15px';
    formStepsContainer.style.borderRadius = '8px';
    formStepsContainer.style.boxShadow = '0 2px 10px rgba(0,0,0,0.05)';
    
    // Default step titles and icons (can be overridden with data attributes)
    const defaultStepTitles = ['Personal Information', 'Organization Information','Document Information', 'Security & Compliance'];
    const defaultStepIcons = ['user', 'file-alt', 'lock'];
    
    // Get custom step titles and icons if available
    const customTitles = document.querySelector('form').dataset.stepTitles;
    const customIcons = document.querySelector('form').dataset.stepIcons;
    
    // Parse custom values or use defaults
    const stepTitles = customTitles ? customTitles.split(',') : defaultStepTitles;
    const stepIcons = customIcons ? customIcons.split(',') : defaultStepIcons;
    
    // Create step buttons
    for (let i = 0; i < formSections.length; i++) {
        const stepBtn = document.createElement('button');
        stepBtn.type = 'button';
        stepBtn.className = i === 0 ? 'step-btn active' : 'step-btn';
        stepBtn.dataset.step = i;
        stepBtn.style.border = 'none';
        stepBtn.style.background = 'transparent';
        stepBtn.style.padding = '8px 15px';
        stepBtn.style.borderRadius = '20px';
        stepBtn.style.fontWeight = 'bold';
        stepBtn.style.color = '#495057';
        stepBtn.style.cursor = 'pointer';
        stepBtn.style.transition = 'all 0.3s';
        stepBtn.innerHTML = `<i class="fas fa-${stepIcons[i]} me-2"></i> ${i+1}. ${stepTitles[i]}`;
        
        stepBtn.addEventListener('click', function() {
            showStep(parseInt(this.dataset.step));
        });
        
        formStepsContainer.appendChild(stepBtn);
    }
    
    // Insert steps navigation before the form
    const form = document.querySelector('form');
    form.parentNode.insertBefore(formStepsContainer, form);
    
    // Add Next/Previous buttons to each section
    for (let i = 0; i < formSections.length; i++) {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'navigation-buttons d-flex mt-3';
        
        if (i > 0) {
            const prevBtn = document.createElement('button');
            prevBtn.type = 'button';
            prevBtn.className = 'btn btn-outline-secondary me-2';
            prevBtn.innerHTML = '<i class="fas fa-arrow-left me-2"></i>Previous';
            prevBtn.addEventListener('click', function() {
                showStep(i-1);
            });
            buttonContainer.appendChild(prevBtn);
        }
        
        if (i < formSections.length - 1) {
            const nextBtn = document.createElement('button');
            nextBtn.type = 'button';
            nextBtn.className = 'btn btn-primary ms-auto';
            nextBtn.innerHTML = 'Next<i class="fas fa-arrow-right ms-2"></i>';
            nextBtn.addEventListener('click', function() {
                showStep(i+1);
            });
            buttonContainer.appendChild(nextBtn);
        }
        
        formSections[i].querySelector('.p-4').appendChild(buttonContainer);
    }
    
    // Initially show only the first section
    showStep(0);
    
    // Function to show a specific step
    function showStep(stepIndex) {
        // Update step buttons
        const stepBtns = document.querySelectorAll('.step-btn');
        stepBtns.forEach((btn, idx) => {
            if (idx === stepIndex) {
                btn.classList.add('active');
                btn.style.background = 'var(--safa-green)';
                btn.style.color = 'white';
            } else {
                btn.classList.remove('active');
                btn.style.background = 'transparent';
                btn.style.color = '#495057';
            }
        });
        
        // Show only the selected section
        formSections.forEach((section, idx) => {
            if (idx === stepIndex) {
                section.style.display = 'block';
                
                // Scroll to the section
                section.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                section.style.display = 'none';
            }
        });
        
        // Show/hide submit button
        const submitBtn = document.querySelector('.btn-submit').parentElement;
        if (stepIndex === formSections.length - 1) {
            submitBtn.style.display = 'block';
        } else {
            submitBtn.style.display = 'none';
        }
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', initFormWizard);

// Multi-step form navigation code we discussed earlier