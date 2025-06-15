document.addEventListener('DOMContentLoaded', function() {
    // Find all SAFA ID generation buttons
    const buttons = document.querySelectorAll('.generate-safa-id');
    
    buttons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const url = this.getAttribute('data-url');
            const targetInput = document.getElementById(targetId);
            const button = this;
            
            // Disable button while processing
            button.disabled = true;
            button.textContent = 'Generating...';
            
            // Make AJAX request to generate ID
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        targetInput.value = data.safa_id;
                        // Add visual feedback
                        targetInput.style.backgroundColor = '#e8f7e8';
                        setTimeout(() => {
                            targetInput.style.backgroundColor = '';
                        }, 1500);
                    } else {
                        console.error('Error generating SAFA ID:', data.error);
                        alert('Failed to generate SAFA ID: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while generating SAFA ID');
                })
                .finally(() => {
                    // Re-enable button
                    button.disabled = false;
                    button.textContent = 'Generate SAFA ID';
                });
        });
    });
});
